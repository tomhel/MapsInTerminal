# MapsInTerminal
A WMS client for the terminal.

MapsInTerminal is a simple command line utility to view maps in the terminal using a WMS service.

Supports WMS version 1.1.1 and 1.3.0. Might work with other versions, but that is untested.

Tested on GNU/Linux, but might work on other Operating Systems aswell.

## License
Mozilla Public License, v. 2.0

## Usage

```
mapsint http://some-wms-service/my/wms mylayer --crs epsg:3857 --center 1750000,8650000
```
#### Controls
Pan: arrow keys<br/>
Zoom: +/-<br/>
Reset view: backspace<br/>
Exit: escape<br/>

#### More advanced options includes:
* WMS version
* WMS format
* WMS styles
* image gutter
* image scaling
* authentication
* axis order
* resolution (units/pixel)

To see all options run: ``` mapsint --help ```

It is possible to set default values for options by creating a file named ``` .MapsInTerminal ``` in the user's home directory:
```json
{
   "crs": "EPSG:3006",
   "format": "image/png",
   "style": null,
   "version": "1.1.1",
   "center": "593000,6902000",
   "res": 2048,
   "gutter": 0,
   "scaling": 1,
   "auth": null,
   "invert": false
}
```

## Dependencies

* python 2.7
* requests
* Pillow
* pager
* img2txt.py

## Installation
```
cd MapsInTerminal
pip install .
```
