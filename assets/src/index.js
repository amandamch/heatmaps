import { handleFileInput } from "./conversions";

let map;

// This is the main function that uses the handleFileInput and initMap
// handleFileInput is kept separate as it is preprocessing data before use on the map
// The map setup function is kept below
const result = async () => {
  // Get the GeoJSON version of the user uploaded file
  const fileResult = await handleFileInput();

  // Display map and reset option, and disable form interaction so user cannot upload a different file unless they reload
  initMap(fileResult);
  document.getElementById('formFileLg').style.pointerEvents = 'None';
  document.getElementById('formFileLg').style.backgroundColor = 'LightGray';
}

result();


// Below is the function that initialises the map using the Google Maps API, and centres the map on the first coordinate
// It also sends a set of coordinates to the form so that we have some pitch corners in Python
function initMap(fileResult) {

  // Get coordinates to centre map around
  var coords = fileResult.features[0].geometry.coordinates[0];
  var getLat = coords[1];
  var getLong = coords[0];

  // Initalises the map with centred coordinates, default as satellite so you can see pitch lines
  map = new google.maps.Map(document.getElementById("mapResult"), {
    zoom: 19,
    center: { lat: getLat, lng: getLong },
    mapTypeId: 'satellite'
  });

  // Sets the style of the GeoJSON data to be a thick yellow blob
  map.data.setStyle({
    strokeColor: 'yellow',
    strokeWeight: 5,
    strokeOpacity: 0.4
  });

  // Sets the details for the drawing manager so we can draw over the map to set pitch boundaries
  const drawingManager = new google.maps.drawing.DrawingManager({
    drawingMode: google.maps.drawing.OverlayType.POLYLINE,
    drawingControl: true,
    drawingControlOptions: {
      position: google.maps.ControlPosition.TOP_CENTER,
      drawingModes: [
        google.maps.drawing.OverlayType.POLYLINE,
      ],
    },
    polylineOptions: {
      editable: true,
    }
  });

  // Puts the four corners of the pitch into a form element so they can be transferred over to Python
  google.maps.event.addListener(drawingManager, 'polylinecomplete', function(line) {
    drawingManager.setMap(null);

    // need to make sure that the pitch value gets updated every time the coordinates get updated
    // Maybe also get rid of the last coordinate here
    var pitch = line.getPath().getArray().toString();
    document.getElementById("pitchCoords").value = pitch;

    if (line.getPath().getArray().toString() != pitch) {
      console.log("change")
    }
    google.maps.event.addListener(line.getPath(), "set_at", () => {
      var pitch = line.getPath().getArray().toString();
      document.getElementById("pitchCoords").value = pitch;
    })
  });

  // Adds the two layers to the map when it is initialised
  map.data.addGeoJson(fileResult);
  drawingManager.setMap(map);
}
