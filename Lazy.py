from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm, LoginForm, ProvideForm
from flask_sqlalchemy import SQLAlchemy
import os
import numpy as np # Import numpy array library and numpy mask
import numpy.ma as ma # Import numpy mask
import pandas as pd # Import Pandas dataframe library

import rasterio as rio # Import Rasterio, a library for working with geospatial raster data
from rasterio.mask import mask # to mask or clip functionality
#from rasterio.plot import show # functionality to plot
from shapely.geometry import Polygon # Import Shapely to work with polygons

import requests # import requests library for making requests to websites
import re # import Python RegEx library

import plotly.graph_objects as go

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
"""
@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')#, posts=posts)
    # render_template('home.html')
"""
ENV = 'dev'

if ENV == 'dev':
   app.debug = True
   app.config['SQLAlCHEMY_DATABASE_URI'] = 'postgresql://postgres:becode@localhost/test'
   #app.config['SQLAlCHEMY_DATABASE_URI'] = 'postgresql://localhost/test'
else:
   app.debug = False
   app.config['SQLAlCHEMY_DATABASE_URI'] = ''

db = SQLAlchemy(app)

class Plot_Hist(db.Model):
    __tablename__ = 'Search'
    id = db.Column(db.Integer, primary_key = True)
    User = db.Column(db.Text(), unique = True, nullable = False)
    Address = db.Column(db.Text())
    Plot = db.Column(db.JSON())

    def __init__(self,Address,User, Plot):
        self.Address = Address
        self.User = User
        self.Plot = Plot


@app.route("/about")
def about():
    return render_template('about.html', title='About')
    # return render_template('about.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    form = ProvideForm()
    if form.validate_on_submit():
    #if request.method == 'POST':  # this block is only entered when the form is submitted
        #address = request.form.get('address')
        address = form.address.data
        data = test(address)
        db.session.add(data)
        db.session.commit()
        req = requests.get(f"http://loc.geopunt.be/geolocation/location?q={address}&c=1")
        x = req.json()['LocationResult'][0]['Location']['X_Lambert72']
        y = req.json()['LocationResult'][0]['Location']['Y_Lambert72']

        maps = pd.read_csv('/media/becode/EXT/CHMsplit/chm.csv', sep=',')
        maps = maps.filename[(maps.left < x) & (x < maps.right) & (maps.bottom < y) & (y < maps.top)]
        path_open = maps.iloc[0]

        result = re.search("^([A-z- ]+)([0-9]+[A-z]?),[ ]?([0-9]+)[ ]?([A-z]+)", address)
        street = result.group(1)
        nb = result.group(2)
        pc = result.group(3)
        city = result.group(4)
        """Request polygon from API : https://api.basisregisters.dev-vlaanderen.be/v1/percelen/{objectId} 
        and retrieve .json object
        """
        req = requests.get(
            f"https://api.basisregisters.dev-vlaanderen.be/v1/adresmatch?gemeentenaam={city}&straatnaam={street}&huisnummer={nb}&postcode={pc}").json()
        objectId = req["adresMatches"][0]["adresseerbareObjecten"][0]["objectId"]
        req = requests.get(f"https://api.basisregisters.dev-vlaanderen.be/v1/gebouweenheden/{objectId}").json()
        objectId = req["gebouw"]["objectId"]
        req = requests.get(f"https://api.basisregisters.dev-vlaanderen.be/v1/gebouwen/{objectId}").json()
        polygon = [req["geometriePolygoon"]["polygon"]]

        path_chm = path_open
        map_chm = rio.open(path_chm)
        """Mask or clip the polygon shape from the CHM raster data with rasterio mask function, this returns a 
        masked raster file and a transform
        """
        mask_chm, mask_chm_transform = mask(dataset=map_chm, shapes=polygon, crop=True, nodata=0, filled=True, indexes=1)

        polygon = Polygon(polygon[0]['coordinates'][0])
        """I need to exclude 0 values from my masked CHM array to calculate a mean height  so I use numpy mask for masking
         the 0's and hereby create the array 'noZeros', sonp.mean(noZeros) will calculate mean height
        """
        noZeros = ma.masked_values(mask_chm, 0)
        """Create dict with house dimensions: area of ground floor, circumference, mean height(see above), max height 
        and possible floors
        """
        dimensions = {"area[m2] : ": round(polygon.area, 1), "circumference[m] : ": round(polygon.length, 1),
                      "mean height[m] : ": round(ma.mean(noZeros), 1), "max height[m] : ": round(np.max(mask_chm), 1),
                      "floors : ": int((np.max(mask_chm) // 3))}

        # plots a surface plot of the mask from polygon out of CHM
        fig = go.Figure(data=[go.Surface(z=mask_chm)])
        fig.update_layout(title='3D Plot of ' + address, width=750, height=750)
        fig.show()

    return render_template('home.html', title='Home', form=form)  # , posts=posts)
    # render_template('home.html')

if __name__ == '__main__':
    app.run()