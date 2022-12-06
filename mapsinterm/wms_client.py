# -*- coding: utf8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
import requests
import termios
import pager
from contextlib import contextmanager
import argparse
import io
import os
import json
from PIL import Image
import ansi
import urllib3


class WMSService(object):
    def __init__(self, url, layer, frmt, styles, srs, version, center,
                 res, gutter, scaling, auth, invert_axis, ssl_verify):

        if not ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.url = url
        self.layer = layer
        self.format = frmt
        self.srs = srs
        self.styles = styles
        self.version = version
        self.gutter = gutter
        self.scaling = scaling
        self.res = res
        self.org_res = res
        self.center = center
        self.org_center = center
        self.session = requests.Session()
        self.session.auth = auth
        self.last_error = None
        self.invert_axis = invert_axis
        self.ssl_verify = ssl_verify
        self.pan_factor = 0.15

    def pan_left(self):
        self.center = self.center[0] - int(self.res * pager.getwidth() * self.pan_factor * self.scaling), \
                      self.center[1]

    def pan_right(self):
        self.center = self.center[0] + int(self.res * pager.getwidth() * self.pan_factor * self.scaling), \
                      self.center[1]

    def pan_up(self):
        self.center = self.center[0], \
                      self.center[1] + int(self.res * pager.getheight() * self.pan_factor * self.scaling)

    def pan_down(self):
        self.center = self.center[0], \
                      self.center[1] - int(self.res * pager.getheight() * self.pan_factor * self.scaling)

    def zoom_in(self):
        self.res /= float(2)

    def zoom_out(self):
        self.res *= 2

    def reset(self):
        self.center = self.org_center
        self.res = self.org_res

    def get_map(self):
        width, height = pager.getwidth() * self.scaling, pager.getheight() * self.scaling
        minx, miny, maxx, maxy = (self.center[0] - (width / float(2) + self.gutter) * self.res,
                                  self.center[1] - (height / float(2) + self.gutter) * self.res,
                                  self.center[0] + (width / float(2) + self.gutter) * self.res,
                                  self.center[1] + (height / float(2) + self.gutter) * self.res)
        bbox = (miny, minx, maxy, maxx) if self.invert_axis else (minx, miny, maxx, maxy)
        params = {
            "width": int(width + self.gutter * 2),
            "height": int(height + self.gutter * 2),
            "bbox": ",".join(str(x) for x in bbox),
            "layers": self.layer,
            "format": self.format,
            "request": "GetMap",
            "version": ".".join(str(x) for x in self.version),
            "service": "WMS",
            "styles": ""
        }

        if self.version >= (1, 3, 0):
            params["crs"] = self.srs
        else:
            params["srs"] = self.srs

        if self.styles:
            params["styles"] = self.styles

        r = self.session.get(self.url, params=params, verify=self.ssl_verify)

        self.last_error = None

        if r.status_code != 200 or not r.headers.get("Content-Type").startswith("image/"):
            self.last_error = r.text
            return None

        try:
            img = Image.open(io.BytesIO(r.content))
            img = process_image(img, self.gutter, self.scaling)
            return img
        except IOError as e:
            self.last_error = str(e)
            return None


def process_image(img, gutter, scaling):
    width, height = img.size

    if gutter != 0:
        img = img.crop((gutter, gutter, width - gutter, height - gutter))
        width, height = img.size

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    if scaling != 1:
        img = img.resize((int(width / scaling), int(height / scaling)), Image.BICUBIC)

    return img


def draw_image(img):
    width, height = img.size
    sys.stdout.write("\x1b[49m\x1b[K")
    sys.stdout.write(ansi.generate_ANSI_from_pixels(img.load(), width, height, None)[0])
    sys.stdout.write("\x1b[0m\n")
    sys.stdout.flush()


@contextmanager
def setup_terminal():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        new_settings = termios.tcgetattr(fd)
        new_settings[3] &= ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, new_settings)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_settings)


def start_client(service):
    while True:
        img = service.get_map()

        if img is None:
            sys.stdout.write("\n")
            sys.stdout.write(service.last_error or "")
        else:
            draw_image(img)

        sys.stdout.write(
            "[%s, %s]" %
            (("%f" % service.center[0]).rstrip("0").rstrip("."),
             ("%f" % service.center[1]).rstrip("0").rstrip("."))
        )
        sys.stdout.flush()

        try:
            k = pager.getchars()
        except KeyboardInterrupt:
            break

        if k == pager.UP:
            # up
            service.pan_up()
        elif k == pager.DOWN:
            # down
            service.pan_down()
        elif k == pager.RIGHT:
            # right
            service.pan_right()
        elif k == pager.LEFT:
            # left
            service.pan_left()
        elif k == pager.ESC or k == pager.CTRL_C_:
            # exit
            break
        elif len(k) == 1 and ord(k[0]) == ord("+"):
            # +
            service.zoom_in()
        elif len(k) == 1 and ord(k[0]) == ord("-"):
            # -
            service.zoom_out()
        elif len(k) == 1 and ord(k[0]) == 127:
            # backspace
            service.reset()


def create_parser():
    default_conf = load_config()
    description = "MapsInTerminal: A WMS client for the terminal"
    epilog = "PAN: arrow keys, ZOOM: +/-, RESET: backspace, EXIT: escape"
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("url",
                        help="WMS service URL")
    parser.add_argument("layer",
                        help="WMS layer")

    parser.add_argument("-c", "--crs", dest="crs", default=default_conf["crs"],
                        help="CRS. Default: %s" % default_conf["crs"])
    parser.add_argument("-f", "--format", dest="format", default=default_conf["format"],
                        help="WMS image format. Default: %s" % default_conf["format"])
    parser.add_argument("-s", "--styles", dest="styles", default=default_conf["styles"],
                        help="WMS layer styles. Default: %s" % default_conf["styles"])
    parser.add_argument("-v", "--version", dest="version", default=default_conf["version"],
                        help="WMS version. Default: %s" % default_conf["version"])

    parser.add_argument("-C", "--center", dest="center", default=default_conf["center"],
                        help="Center coordinate, easting,northing. Default: %s" % default_conf["center"])
    parser.add_argument("-R", "--res", type=float, dest="res", default=default_conf["res"],
                        help="resolution, units/pixel. Default: %f" % default_conf["res"])
    parser.add_argument("-G", "--gutter", type=int, dest="gutter", default=default_conf["gutter"],
                        help="Image gutter in pixels. Default: %d" % default_conf["gutter"])
    parser.add_argument("-S", "--scaling", type=float, dest="scaling", default=default_conf["scaling"],
                        help="Image scale factor. Default: %f" % default_conf["scaling"])
    parser.add_argument("-A", "--auth", dest="auth", default=default_conf["auth"],
                        help="Authentication, user:password. Default %s" %
                             (None if default_conf["auth"] is None else default_conf["auth"].split(":")[0] + ":*****"))
    parser.add_argument("-I", "--invert", action="store_false" if default_conf["invert"] is True else "store_true",
                        dest="invert", default=default_conf["invert"],
                        help="Invert axis order. Default %s" % default_conf["invert"])
    parser.add_argument("-n", "--no-ssl-verify", action="store_false",
                        dest="ssl_verify", default=default_conf["ssl_verify"],
                        help="Disable SSL certificate verification. Default %s"
                             % "enabled" if default_conf["ssl_verify"] is True else "disabled")
    return parser


def load_config():
    conf_file = os.path.join(os.path.expanduser("~"), ".MapsInTerminal")
    conf = {
        "crs": "EPSG:3857",
        "format": "image/png",
        "styles": None,
        "version": "1.1.1",
        "center": "2044638,8251379",
        "res": 1222.992452562820,
        "gutter": 0,
        "scaling": 1,
        "auth": None,
        "invert": False,
        "ssl_verify": True
    }

    if os.path.isfile(conf_file):
        with open(conf_file) as f:
            conf.update(json.load(f))

    return conf


def main():
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    center = tuple(float(x) for x in args.center.split(","))
    auth = None if args.auth is None else tuple(args.auth.split(":"))
    version = tuple(int(x) for x in args.version.split("."))

    with setup_terminal():
        service = WMSService(args.url, args.layer, args.format, args.styles, args.crs, version,
                             center, args.res, args.gutter, args.scaling, auth, args.invert, args.ssl_verify)
        start_client(service)


if __name__ == "__main__":
    sys.exit(main())
