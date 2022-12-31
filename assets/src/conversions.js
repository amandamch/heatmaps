// requiring functions from @tcmw/togeojson
// CommonJS require is not browser compatible, so the modules have been bundled with webpack
const tj = require("../node_modules/@tmcw/togeojson");

// neither node nor togeojson have xml parsing or a dom., so we use @xmldom/xmldom
const DOMParser = require("../node_modules/@xmldom/xmldom").DOMParser;

// Creating two different HTML protoypes to be used as asynchronous event listeners using promises
// This lets me wait for events without nesting even listeners and losing the result
HTMLElement.prototype.waitForFile = function (){
    return new Promise ((resolve) => {
        this.addEventListener("change", () => {
            resolve();
        });
    });
};

FileReader.prototype.waitForLoad = function (){
    return new Promise ((resolve) => {
        this.addEventListener("load", () => {
            resolve();
        });
    });
};

// creating a new filereader object to be used inside the function
var fileReader = new FileReader();

// Function takes a file input, and once it has loaded, converts the file into a GeoJSON feature collection

export async function handleFileInput() {
    let target = document.getElementById("formFileLg");
    if (target === null){
        return;
    }
    await target.waitForFile();
    let fileInput = document.getElementById("formFileLg").files[0];
    fileReader.readAsText(fileInput);
    await fileReader.waitForLoad();
    let textFile = fileReader.result;
    const dom = new DOMParser().parseFromString(textFile, "text/xml");
    const fileAsGeoJSON = convertFile(fileInput, dom);
    return fileAsGeoJSON;
    
    // this is the bit that does the actual converting, by determining the file type and then converting to geojson with the module
    function convertFile(fileInput, dom) {
        var fileName = fileInput.name;
        var fileType = fileName.split('.').pop();
        if (fileType === "gpx") {
            const converted = tj.gpx(dom);
            return converted;
        } else if (fileType === "tcx") {
            const converted = tj.tcx(dom);
            return converted;
        } else {
            alert("This file doesn't seem to be compatible! Please ensure you have uploaded a .gpx or .tcx file only.")
            throw new Error("Unexpected error- please report");
        }
    }
}