# Rugby Heatmap Generator

## Who?
Created by me (and me alone)

## What?
The current repository represents an almost-finished program, written predominantly in Python and JavaScript. The program, which is designed to be used on the web, takes a .tcx/.gpx file from a user, such as can be downloaded from FitBit, Strava, Garmin, etc. (with the two file formats covering the majority of outputs from fitness software), with the eventual aim of displaying a heatmap of activity for the user.

The first step after the file upload is to take the data, convert it to GeoJSON for use with the Google Maps API, and then display the data on a satellite map, which is automatically generated on file upload. This is done with the conversions.js file, which uses asynchronous programming to achieve this. The next step involves the user clicking on the map to draw a polyline that creates the four corners of the sports pitch (specifically rugby, for reasons to be explained later), with the corners made draggable so that the user can alter their clicks if they are not quite correct. Once that has been done, the array of coordinates, and the original file data, is passed to Flask.

This is where the Flask app kicks in, although there is still more expansion needed in the future. The Flask app reads the array of coordinates literally as tuples, and these are used as the Cartesian coordinates for the maths that then happens. Firstly, the southernmost coordinate is determined, followed by the closest and furthest coordinates, with the coordinate for the other end of the adjacent long side of the rectangle from the southernmost determined as the coordinate in between those. Once these have been found, the distances between the points are calculated with geopy, and a little bit of trigonometry is done to determine the angle of rotation of the pitch, assuming that the short side will be the bottom of the pitch, and the long side is roughly at a right angle to the short side.

Following this, the data is rotated according to the angle of transformation, and then displayed using a Seaborn KDE plot. This current version also shows what will become a text box to show information about speed, duration, and pitch dimensions, for the purpose of communicating those to a user. These variables have already been calculated in the code.

In this project, I used:
- Asynchronous javascript processing, to fire functions only when a user had uploaded a file
- Within this, promise syntax and Javascript Element Prototypes to introduce new functions to objects
- Modular Javascript, to allow myself to organise my project
- Javascript modules, using 'require'
- Since browsers do not use 'require', I also used a webpack bundler to bundle the JavaScript so it could be used in a web app
- Google Maps API in JavaScript, using the drawingManager, data layer, and basic init functions to display user data on a map after they uploaded their file; the way I used these libraries was not in the 'out of the box' fashion, since I had to modify functions to suit my needs
- Restricting API Keys for my own use
- Flask; specifically getting Flask to work with a Webpack bundler (and vice versa)
- Secure ssl in Flask to run the API on https://
- Passing data acquired through interaction with form data back to a form through Javascript, and re-interpreting the Javascript data in python for use in Flask
- Maths/trig with geodesic coordinates
- Transforming coordinate data to create maps
- Jinja2 templating
- Matplotlib and Seaborn libraries

## Where?
Somewhere in the depths of the rainy UK

## When?
This project was started in November 2022, with the aim of completing Harvard University's CS50 course. Since then, I have been developing this project and it is nearly ready for testing. The final stages are creating the information box (and making it align with the pitch on the page), making this appear as an image in the results page (with options to download), and error handling/user testing.

## Why?
GPS sports data, like Opta and StatSports, can be very expensive and inaccessible, particularly to grassroots teams. As someone who is a big fan of data, particularly relating to sport, I found this disappointing, and wanted to use my CS50 knowledge (and my numpy/pandas knowledge from my master's) to rectify this. With this program, a user could create and record GPS data even on their phone, or any GPS-enabled device (hence the two different file formats) that can record sports activity (without having to buy a new device!) and create activity heatmaps for their exercise, for free. The reason this is for rugby is simple: I'm a rugby player, and having been used to lots of useful stats when I was a rower, I wanted more out of my game, so I built this tool specifically for rugby. Plus, mapping the lines on a rugby pitch is easy since there's no boxes or semicircles!
