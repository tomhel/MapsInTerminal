# MapsInTerminal
A WMS client for the terminal.

MapsInTerminal is a simple command line utility to view maps in the terminal using a WMS service.

Supports WMS version 1.1.1 and 1.3.0. Might work with other versions, but that is untested.

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

## Dependencies

* python 2.7
* requests
* Pillow
* pager
* img2txt.py

## Installation
```
cd MapsInTerminal
pip install -r requirements.txt .
```
