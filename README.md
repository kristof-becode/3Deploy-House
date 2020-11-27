# 3Deploy House

Deployment of my 3D House programme to Heroku. This app creates 3D plots of houses and buildings in the city centre of Ghent.

Try the app here: https://plothouse.herokuapp.com/

<table>
  <tr>
    <td><img src="https://github.com/kristof-becode/3Deploy-House/blob/master/img/HerokuDeploy1.png" width=100% height=100%/></td>
    <td><img src="https://github.com/kristof-becode/3Deploy-House/blob/master/img/HerokuDeploy2.png" width=100% height=100%/></td>
  </tr>
 </table>

### Table of contents

* [Intro](#intro)
* [Packages used](#packages-used)
* [What is a CHM?](#what-is-a-chm)
* [How does it work?](#how-does-it-work)
* [App specifics](#app-specifics)

## Intro

This repo is the deployment of my 3D House project that renders a 3D plot of a house when an address is provided. 
The code for the original 3D House is here: https://github.com/kristof-becode/3D-House

I tweaked the code to deal with errors in the API requests for Lambert-72 coordinates and polygon shapes. For size reduction in deploying I restricted the addresses from which to plot a house to the city centre of Ghent, Belgium. The original code worked for the whole of Flanders but needed about 80 Gb of storage space for >1000 Canopy Height Models. This Flask app uses only 9 CHM geotiff raster files, each about 4Mb in size, to cover the Ghent city centre.

The 9 CHMs for Ghent city centre stitched together:
<p align="center">
  <img src="https://github.com/kristof-becode/3Deploy-House/blob/master/img/stitchedCHMs.png" width=50% >
</p>

## Packages used

- Numpy: a scientific computation package
- Pandas: a data analysis/manipulation tool using dataframes
- Rasterio: GDAL and Numpy-based library to work with geospatial data
- Shapely: a package for manipulation and analysis of planar geometric objects
- Plotly: a plotting libary
- Flask: a micro web framework to build web apps
- Heroku: a container-based cloud platform for deployment

## What is a CHM?

The app uses Canopy Height Model raster files. These were produced by retrieving Lidar created Digital Terrain Models and Digital Surface Models from a Flanders government website. Subtracting the DTM from the DSM Geotiff raster files results in the Canopy Height Model that contains the height or residual distance between the ground and the top of the of objects above the ground. This includes the actual heights of trees, buildings and any other objects on the earth’s surface. 

## How does it work?

- Make an API request for Lambert-72 coordinates for a provided address (+ verify that the address is in 1 of my 9 CHM maps)
- Find the Canopy Height Model that contains these coordinates out of 9 for city centre Ghent
- Make an API request for the polygon coordinates related to the given address
- Create a polygon shape and mask the selected CHM with it; we have now effectively cut out the house from the CHM raster file
- Make some house dimension estimates from this mask
- Render a surface plot of this mask..et voilà, there is the 3D house plot! 

## App specifics

I selected 9 CHM maps to span the area of the city centre of Ghent and I also merged them to make the city aerial view image above, see the 2 corresponding Jupyter notebooks. 

As I reran the code I noticed it needed some extra work to handle non-existing addresses and faulty returns from the API calls so I made sure to implement these changes. Restriction of input addresses to Ghent city centre was also implemented. 

A simple Flask app was built around the code with HTML and CSS. The 3d plot that is rendered with Plotly is written out as a ```div``` section and inserted into an HTML template so it actually renders in the app when deployed to Heroku. 

The code for the app can be found in the ```plothouse/3dhouse.py```.



