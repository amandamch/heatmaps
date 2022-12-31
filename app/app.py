from ast import literal_eval
import math
import geopy, geopy.distance
import numpy as np
from flask import Flask, render_template, request
from asset import Asset
#Initialises extension from asset.py

app = Flask(__name__)
Asset(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/result", methods=["GET", "POST"])
def result():
    if request.method == "POST":
        # Step 1- figure out the how the pitch is laid out, and the angle to transform the data by
        # Extract tuples of pitch coordinates from form and find southernmost coordinate to use as bottom left/right
        pitchCoords = literal_eval(request.form.get("pitchCoords"))
        southernmost = (90, 0)
        closestDistance = 0
        furthestDistance = 0
        longSideDistance = 0
        closest = None

        for coord in pitchCoords:
            if coord[0] < southernmost[0]:
                southernmost = coord
                southernmostIndex = pitchCoords.index(coord)

        # Calculating closest and furthest coordinate with geodesic distance
        for coord in pitchCoords:
            distance = geopy.distance.distance(coord, southernmost).meters
            if distance < closestDistance and distance != 0 or closestDistance == 0:
                closestDistance = distance
                closestIndex = pitchCoords.index(coord)
                closest = coord
            if distance > furthestDistance:
                furthestDistance = distance

        # Keeping this separate otherwise we can get a 0 distance, if southernmost is 0 and closest is 3
        # There's definitely a better way of doing this though! I don't like that this is a copy-paste from the other loop
        for coord in pitchCoords:
            distance = geopy.distance.distance(coord, southernmost).meters
            if distance < furthestDistance and distance > closestDistance:
                longSideDistance = distance

        # Creating an imaginary adjacent line to do trig with- closest-southernmost exists as a hypotenuse
        adjacentLat = float(southernmost[0])
        adjacentLong = float(closest[1])
        adjacentCoord = (adjacentLat, adjacentLong)
        adjacentLength = geopy.distance.distance(adjacentCoord, southernmost).meters
        
        transformAngle = math.acos(adjacentLength / closestDistance)
        angles = math.degrees(transformAngle)
        
        origin = None

        if southernmost[1] < closest[1]:
            transformAngle = -transformAngle
            origin = southernmost
        else:
            origin = closest
        # need to know if closest is left or right of southernmost
        # then clockwise transform can be made clockwise
        
        # if oppo > 0 we do one thing and if oppo > 0 we do another - I think we need to put the top speed/etc at the top here
        # For CS50, I think just produce the scatter graph and then just do something later



        file = request.files.get('file')
        return render_template("result.html", closestDistance=closestDistance, longSideDistance=longSideDistance, transformAngle=transformAngle, angles=angles, origin=origin)
    else:
        print("This will print an error message once I get round to it")


if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'))