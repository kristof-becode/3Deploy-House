"""
Imports
"""
from flask import Flask, render_template, request, flash    # Flask for website rendering
import numpy as np                                          # Data science package for working with arrays
import numpy.ma as ma                                       # Import numpy mask
import pandas as pd                                         # Working with dataframes and reading CSVs
import requests                                             # Requests to web APIs
import os                                                   # System file handling
import re                                                   # Python RegEx
import rasterio as rio                                      # Working with geospatial raster data(GeoTiffs)
from rasterio.mask import mask                              # Masking geotiff raster files and polygon shapes
from shapely.geometry import Polygon                        # Import Shapely to work with polygons
import plotly.graph_objects as go                           # Import Plotly library for 3D plotting

"""
App
"""


app = Flask(__name__)

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'

# Path with CHM maps and the CSV to look up corresponding CHM map for coordinates
CHM_FOLDER = 'static/CanopyHeightMaps/'

"""
Functions to plot house from a provided address in centre of Ghent
"""


"""
Make API call to retrieve Lambert72-coordinates for input address
"""

def retrieve_coords(address):
    req = requests.get(f"http://loc.geopunt.be/geolocation/location?q={address}&c=1")
    x = req.json()['LocationResult'][0]['Location']['X_Lambert72']
    y = req.json()['LocationResult'][0]['Location']['Y_Lambert72']

    return x, y


"""
In a CSV I look up the Canopy Height Model map that contains the coordinates of input address.
I will only allow addresses in the selected 9 CHM tif files in the city centre of Ghent.
"""

def retrieve_map(x, y):
    # Open CSVs with coordinate range per Canopy Height Model map
    csv_path = os.path.join(CHM_FOLDER, 'chm.csv')
    maps = pd.read_csv(csv_path, sep=',')
    # Look up map that contains coordinates x,y for house address
    maps = maps.filename[(maps.left < x) & (x < maps.right) & (maps.bottom < y) & (y < maps.top)]
    chm_open = maps.iloc[0]
    # Check if CHM map is in the list for city centre Ghent
    if chm_open in ['tile_chm_k22_102.tif', 'tile_chm_k22_103.tif', 'tile_chm_k22_104.tif',
                     'tile_chm_k22_134.tif', 'tile_chm_k22_135.tif', 'tile_chm_k22_136.tif',
                     'tile_chm_k22_166.tif', 'tile_chm_k22_167.tif', 'tile_chm_k22_168.tif']:
        #chm_map = os.path.join(CHM_FOLDER, chm_open)
        chm_map = CHM_FOLDER + chm_open

    return chm_map

"""
Make an API call to retrieve polygon shape as .json for a house corresponding to input address
"""

def retrieve_polygon(address):
    # Separate address elements
    result = re.search("^([A-z- ]+)([0-9]+[A-z]?),[ ]?([0-9]+)[ ]?([A-z]+)$", address)
    street = result.group(1)
    nb = result.group(2)
    pc = result.group(3)
    city = result.group(4)
    # Make API call with address elements to return polygon list
    req = requests.get(
        f"https://api.basisregisters.dev-vlaanderen.be/v1/adresmatch?gemeentenaam={city}&straatnaam={street}&huisnummer={nb}&postcode={pc}").json()
    objectId = req["adresMatches"][0]["adresseerbareObjecten"][0]["objectId"]
    req = requests.get(f"https://api.basisregisters.dev-vlaanderen.be/v1/gebouweenheden/{objectId}").json()
    objectId = req["gebouw"]["objectId"]
    req = requests.get(f"https://api.basisregisters.dev-vlaanderen.be/v1/gebouwen/{objectId}").json()
    polygon = [req["geometriePolygoon"]["polygon"]]

    return polygon


"""
With Rasterio mask the earlier retrieved polygon shape for a house from the selected Canopy Height Map that contains 
the house and return mask. We have effictively "cut" out the house from the CHM Geotiff.
"""

def mask_polygon(poly, path):
    path_chm = path
    map_chm = rio.open(path_chm)
    mask_chm, mask_chm_transform = mask(dataset=map_chm, shapes=poly, crop=True, nodata=0, filled=True, indexes=1)

    return mask_chm

"""
Create polygon shape with Shapely Polygon from coordinates of polygon list and calculate estimates 
for house area and circumference. Using Numpy to calculate estimates for mean height, max height, possible floors from
the masked CHM from previous step that contains only the house.
"""

def dim_house(poly, mask_chm):
   # Use Shapely Polygon to create the polygon
    polygon = Polygon(poly[0]['coordinates'][0])
   # Mask zeros in CHM map to calculate mean height below
    noZeros = ma.masked_values(mask_chm, 0)
   # Create dict with house dimensions
    dimensions = {"area[m2] : ": round(polygon.area, 1), "circumference[m] : ": round(polygon.length, 1),
                  "mean height[m] : ": round(ma.mean(noZeros), 1), "max height[m] : ": round(np.max(mask_chm), 1),
                  "floors : ": int((np.max(mask_chm) // 3))}
    # Concatenate all dimensions items into 1 string to print on 3D plot
    dims = ''
    for key, value in dimensions.items():
        dims += str(key) + str(value) + ',\n'

    return dims

"""
Plot a 3d house with Plotly
"""

def D3Plot(address, mask, dimensions):
    # plots a surface plot of the mask from polygon out of CHM
    fig = go.Figure(data=[go.Surface(z=mask)])
    fig.update_layout(title='3D house plot of ' + address + '<br><br>' + dimensions, width=800, height=750)
    # write figure as <div> section, is as string, to be used to plot in the Plot page
    plt_div = fig.to_html(full_html=False, include_plotlyjs='cdn')

    return plt_div


"""
App pages; Home and About
"""

# About page
@app.route("/about")
def about():
    return render_template('about.html', title='About')

# Home page
@app.route('/home')
@app.route('/')
def home():
    return render_template('home.html', title='Home')

# Plot page
@app.route("/plot")
def plot():
    return render_template('plot.html', title='plot')

# Action: PLot page back to Home
@app.route('/back', methods= ['POST','GET'])
def back():
    return render_template('home.html', title='Home')

# Home page actions on address input; call functions above to plot house at provided address
@app.route('/address_in', methods= ['POST','GET'])
def address_in():
    address = request.form['address']  # get
    if not (re.match("^([A-z-]+)\s([0-9]+[A-z]?),\s([0-9]+)\s([A-z]+)$", address)):  # Verify address input format
        flash('That is an invalid address format! Try again.', "info")
        return render_template('home.html', title='Home')
    else:
        try:
            x, y = retrieve_coords(address)
            path = retrieve_map(x, y)
            poly = retrieve_polygon(address)
            mask_chm = mask_polygon(poly, path)
            dimensions = dim_house(poly, mask_chm)
            plotfig = D3Plot(address, mask_chm, dimensions)
            return render_template('plot.html', title='plot', toplot=plotfig)

        # Capture all possible exceptions in functions
        except:
            flash('You typed in an non-existing address or an address outside the range of this app! Try again.')
            return render_template('home.html', title='Home')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')