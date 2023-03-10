from ast import literal_eval
import math
import numpy as np
import geopy, geopy.distance
import gpxpy, gpxpy.gpx
from tcxreader.tcxreader import TCXReader
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, abort
from asset import Asset
from werkzeug.utils import secure_filename
import tempfile
import seaborn as sns
import datetime
import base64
from io import BytesIO

UPLOAD_FOLDER = tempfile.mkdtemp()
app = Flask(__name__)
Asset(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
# TODO: try/except for this route, leading to error page if there's an error
def index():
    return render_template("index.html")

@app.route("/result", methods=["GET", "POST"])
def result():
    try:
        if request.method == "POST":
            # Step 1- figure out the how the pitch is laid out, and the angle to transform the data by
            # Extract tuples of pitch coordinates from form and find southernmost coordinate to use as bottom left/right
            pitchCoords = literal_eval(request.form.get("pitchCoords"))
            southernmost = (90, 0)
            closestDistance = 0
            furthestDistance = 0
            longSideDistance = 0
            longSide = None
            closest = None
            origin = None
            furthest = None

            if len(pitchCoords) != 5:
                return render_template("errorpage.html", undefined=" you didn't have the right number of corners on your pitch")
            
            for coord in pitchCoords:
                if coord[0] < southernmost[0]:
                    southernmost = coord

            # Calculating closest and furthest coordinate with geodesic distance
            # TODO: Need to control for people accidentally dragging one of the polyline ends
            for coord in pitchCoords:
                distance = geopy.distance.distance(coord, southernmost).meters
                if distance < closestDistance and distance > 1 or closestDistance == 0:
                    closestDistance = distance
                    closest = coord
                if distance > furthestDistance:
                    furthestDistance = distance
                    furthest = coord

            # Keeping this separate otherwise we can get a 0 distance, if southernmost is 0 and closest is 3
            # There's definitely a better way of doing this though! I don't like that this is a copy-paste from the other loop
            for coord in pitchCoords:
                distance = geopy.distance.distance(coord, southernmost).meters
                if distance < furthestDistance and distance > closestDistance:
                    longSide = (coord[1], coord[0]) # (x, y) orientation rather than lat/long
                    longSideDistance = distance

            # Creating an imaginary adjacent line to do trig with- closest-southernmost exists as a hypotenuse
            adjacentLat = float(southernmost[0])
            adjacentLong = float(closest[1])
            adjacentCoord = (adjacentLat, adjacentLong)
            adjacentLength = geopy.distance.distance(adjacentCoord, southernmost).meters
            transformAngle = math.acos(adjacentLength / closestDistance)

            # If southernmost is west of closest, the origin is southernmost and we rotate clockwise
            # If southernmost is east of closest, the origin is closest and we rotate anticlockwise
            # Before using it to rotate, we also need to swap the values, so that it is an (x, y) coord not lat/long which is (y, x)
            if southernmost[1] < closest[1]:
                transformAngle = -transformAngle
                origin = (southernmost[1], southernmost[0])
                closest = (closest[1], closest[0])
            else:
                origin = (closest[1], closest[0]) # origin is the closest point to southernmost
                closest = (southernmost[1], southernmost[0]) # reassigning closest to be at southernmost
                longSide = (furthest[1], furthest[0]) # longside is now where furthest is
                anticlockwise = True
            
            file = request.files['file']
            filename = file.filename
            secureFilename = secure_filename(filename)
            coordsArray = [] # Array to store coordinates extracted from file to iterate through and rotate, passing result to xData/yData
            xData = []
            yData = []
            totalDist = 0
            totalTime = 0
            maxSpeed = 0
            avgSpeed = 0

            #Step 2: Iterating through the different files using parsers and extracting the information that we need
            if filename.split('.')[-1] == 'gpx':
                # Save GPX file to the temp folder that we set up in the app.config
                file.save(app.config['UPLOAD_FOLDER'] + secureFilename)

                # Open, parse and extract coordinates
                with open(app.config['UPLOAD_FOLDER'] + secureFilename, "r") as gpxFile:
                    gpx = gpxpy.parse(gpxFile)
                    for track in gpx.tracks:
                        for segment in track.segments:
                            for point in segment.points:
                                newCoord = (float(point.latitude), float(point.longitude))
                                coordsArray.append(newCoord)
                    
                    # Extracting general stats for display below the heatmap
                    # NOTE: gpxpy's get_duration and length_3d methods remove the top 5% of speeds and distances, under the assumption that they are GPS errors
                    # This is highly likely, and so the data reflected in this parser is likely to be more accurate than strava, which makes its calculations on raw data
                    totalDist = gpx.length_3d()
                    totalTime = gpx.get_duration()
                    maxSpeed = gpx.get_moving_data().max_speed
                    avgSpeed = float(totalDist) / float(totalTime)

            elif filename.split('.')[-1] == 'tcx':
                # Save TCX file to the temp folder that we set up in the app.config
                file.save(app.config['UPLOAD_FOLDER'] + secureFilename)

                # Open, parse and extract coordinates
                tcxReader = TCXReader()
                fileLocation = app.config['UPLOAD_FOLDER'] + secureFilename
                tcx = tcxReader.read(fileLocation)
                for trackpoint in tcx.trackpoints:
                    # KNOWN 500 ERROR- one activity with whitespace at start of title caused "xml.etree.ElementTree.ParseError: XML or text declaration not at start of entity"
                    # Unclear if this is an error common to activities with whitespace at the start of title- to investigate further
                    newCoord = (float(trackpoint.latitude), float(trackpoint.longitude))
                    coordsArray.append(newCoord)

                # NOTE: TCXReader operates on raw data, which is different from gpxpy, since TCX files provide the raw data to extract, rather than needing a parser to calculate
                totalDist = tcx.distance
                totalTime = tcx.duration
                maxSpeed = tcx.max_speed
                avgSpeed = tcx.avg_speed

            else:
                print("File Type Error: please report")
                abort(400)

            # Step 3: Transform the extracted data and display it as a heatmap on the pitch, responsive to the pitch's size
            # Setting up a function that will allow us to rotate a point about another
            def rotate(origin, point, angle):
                ox, oy = origin
                px, py = point

                qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
                qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)

                return qx, qy
            
            maxAxisTop = rotate(origin, longSide, transformAngle) # Top
            maxAxisBottom = rotate(origin, closest, transformAngle) # Bottom
            # NOTE: For some reason, the rotation of these coordinates on the x axis aren't working, so I used the origin for the leftmost limit and did some ratio maths for the right one

            for coord in coordsArray:
                coord = (coord[1], coord[0]) # Change orientation from (lat, long) to (x, y)
                newPoint = rotate(origin, coord, transformAngle)
                xData.append(float(newPoint[0])) # Append longitude
                yData.append(float(newPoint[1])) # Append latitude

            # To try and get around the x axis rotation issue for just the coordinate points (weird), we're going to use the ratio of coordinates to metres from the y axis
            # This operates on the assumption that the proportion of metres to coordinates is the same for both sides, which may need some consideration regarding geodesic distance
            # This is in the works and will be worked on, but the small scale of the data (rugby pitch vs globe) make this a minor concern in relation to communicating data
            oneMetre = (maxAxisTop[1] - maxAxisBottom[1]) / float(longSideDistance)
            farSide = oneMetre * closestDistance
            maxRight = origin[0] + farSide

            fig, axs = plt.subplots(1, 2, height_ratios=[1])
            fig.subplots_adjust(wspace=0)

            xData = np.array(xData)
            yData = np.array(yData)

            sns.kdeplot(x=xData, y=yData, ax=axs[0], fill="True", cmap="inferno", levels=100)

            axs[0].set_box_aspect(float(longSideDistance) / float(closestDistance))
            axs[0].set_xlim(origin[0], maxRight)
            axs[0].set_ylim(maxAxisBottom[1], maxAxisTop[1])
            axs[0].set_xticks([])
            axs[0].set_yticks([])
            axs[0].set_facecolor('xkcd:grass green')

            # All map plots have a halfway line, with the following added if conditions are met:
            # end to end > 20 metres: 5m from try line (dashed)
            # > 40 metres: 10m from halfway (dashed)
            # > 72 metres: 22m from try line (solid)
            halfwaY = maxAxisBottom[1] + ((maxAxisTop[1] - maxAxisBottom[1]) / 2)
            axs[0].axhline(y=halfwaY, xmin=0, xmax=1, c='w')

            if longSideDistance > 20:
                fiveMetres = 5 * ((maxAxisTop[1] - maxAxisBottom[1]) / longSideDistance)
                axs[0].axhline(y=(maxAxisBottom[1] + fiveMetres), xmin=0, xmax=1, c='w', linestyle='dashed')
                axs[0].axhline(y=(maxAxisTop[1] - fiveMetres), xmin=0, xmax=1, c='w', linestyle='dashed')

            if longSideDistance > 40:
                tenMetres = 10 * ((maxAxisTop[1] - maxAxisBottom[1]) / longSideDistance)
                axs[0].axhline(y=(halfwaY + tenMetres), xmin=0, xmax=1, c='w', linestyle='dashed')
                axs[0].axhline(y=(halfwaY - tenMetres), xmin=0, xmax=1, c='w', linestyle='dashed')
            
            if longSideDistance > 72:
                twenty2 = 22 * ((maxAxisTop[1] - maxAxisBottom[1]) / longSideDistance)
                axs[0].axhline(y=(maxAxisBottom[1] + twenty2), xmin=0, xmax=1, c='w')
                axs[0].axhline(y=(maxAxisTop[1] - twenty2), xmin=0, xmax=1, c='w')

            axs[1].set_xlim(origin[0], maxRight)
            axs[1].set_ylim(maxAxisBottom[1], maxAxisTop[1])
            axs[1].axis('off')
            axs[1].set_box_aspect(1.5) # 1.5 times taller than it is wide, so we always have space for the text

            # then start with the text- we want 5 pieces of text, so we want to create our label font and divide the space into 6 lengthwise and then create an indent
            font = {'family':'sans-serif', 'color':'#2C4251', 'size':10}
            oneSixth = float(maxAxisTop[1] - maxAxisBottom[1]) / 6
            indent = origin[0] + (float(maxRight - origin[0]) / 10)

            axs[1].text(indent, (maxAxisTop[1] - oneSixth), 'Pitch Dimensions: {length:.2f}m x {width:.2f}m'.format(length=longSideDistance, width=closestDistance), fontdict=font)
            axs[1].text(indent, (maxAxisTop[1] - 2*oneSixth), 'Elapsed Time: {time}'.format(time=datetime.timedelta(seconds=totalTime)), fontdict=font)
            axs[1].text(indent, (maxAxisTop[1] - 3*oneSixth), 'Total Distance: {dist:.0f}m'.format(dist=totalDist), fontdict=font)
            axs[1].text(indent, (maxAxisTop[1] - 4*oneSixth), 'Average Speed: {speed:.2f}m/s'.format(speed=avgSpeed), fontdict=font)
            axs[1].text(indent, (maxAxisTop[1] - 5*oneSixth), 'Max Speed: {speed:.2f}m/s'.format(speed=maxSpeed), fontdict=font)

            fig.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, dpi='figure', format='png', edgecolor='#2C4251')
            data = base64.b64encode(buf.getbuffer()).decode("ascii")

            return render_template("result.html", data=f'data:image/png;base64,{data}')
        else:
            print("Page accessed incorrectly; returning home")
            return render_template("index.html")
    except:
        return render_template("errorpage.html", undefined="something went wrong with your file upload")


if __name__ == "__main__":
    app.run()