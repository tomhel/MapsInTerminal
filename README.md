# MapsInTerminal
A WMS client for the terminal.

MapsInTerminal is a simple command line utility to view maps in the terminal using a WMS service.

Supports WMS version 1.1.1 and 1.3.0. Might work with other versions, but that is untested.

Tested on GNU/Linux, but might work on other Operating Systems aswell.

## License
Mozilla Public License, v. 2.0

## Usage

### Web Mercator projection

This is the default projection.

```
mapsint http://some-wms-service/my/wms mylayer
```

### Official projection of Sweden

Use a custom projection.

```
mapsint http://some-wms-service/my/wms mylayer --crs epsg:3006 --center 593000,6902000
```

### OpenStreetMap

Can be used with OpenStreetMap WMS provided by [terrestris](https://www.terrestris.de/en/openstreetmap-wms/)

```
mapsint https://ows.terrestris.de/osm/service OSM-WMS --no-ssl-verify
```

[![wms_osm](wms_osm_mini.png?raw=true)](wms_osm.png?raw=true)

(_Map data from [OpenStreetMap](https://www.openstreetmap.org/copyright)_)


### Controls
Pan: arrow keys<br/>
Zoom: +/-<br/>
Reset view: backspace<br/>
Exit: escape<br/>

### More advanced options includes:
* WMS version
* WMS format
* WMS styles
* image gutter
* image scaling
* authentication
* axis order
* resolution (units/pixel)
* SSL certificate verification

To see all options run: ``` mapsint --help ```

It is possible to set default values for options by creating a file named ``` .MapsInTerminal ``` in the user's home directory:
```json
{
   "crs": "EPSG:3857",
   "format": "image/png",
   "styles": null,
   "version": "1.1.1",
   "center": "2011618,8251379",
   "res": 2048,
   "gutter": 0,
   "scaling": 1,
   "auth": null,
   "invert": false,
   "ssl_verify": true
}
```

## Dependencies

* Python 3
* requests
* Pillow
* pager
* img2txt.py

## Installation
```
cd MapsInTerminal
pip install .
```
