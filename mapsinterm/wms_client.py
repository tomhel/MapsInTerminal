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
from PIL import Image
import ansi


class WMSService(object):
    def __init__(self, url, layer, frmt, style, srs, version, center,
                 res, gutter, scaling, auth, invert_axis):
        self.url = url
        self.layer = layer
        self.format = frmt
        self.srs = srs
        self.style = style
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
            "service": "WMS"
        }

        if self.version >= (1, 3, 0):
            params["crs"] = self.srs
        else:
            params["srs"] = self.srs

        if self.style:
            params["style"] = self.style

        r = self.session.get(self.url, params=params)

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
    description = "A WMS client for the terminal"
    epilog = "PAN: arrow keys, ZOOM: +/-, RESET: backspace, EXIT: escape"
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument("url",
                        help="WMS service URL")
    parser.add_argument("layer",
                        help="WMS layer")

    parser.add_argument("-c", "--crs", dest="crs", default="EPSG:3006",
                        help="CRS. Default: EPSG:3006")
    parser.add_argument("-f", "--format", dest="format", default="image/png",
                        help="WMS image format. Default: image/png")
    parser.add_argument("-s", "--style", dest="style", default=None,
                        help="WMS layer style")
    parser.add_argument("-v", "--version", dest="version", default="1.1.1",
                        help="WMS version. Default: 1.1.1")

    parser.add_argument("-C", "--center", dest="center", default="593000,6902000",
                        help="Center coordinate, easting,northing. Default: 593000,6902000")
    parser.add_argument("-R", "--res", type=float, dest="res", default=2048,
                        help="resolution, units/pixel. Default: 2048")
    parser.add_argument("-G", "--gutter", type=int, dest="gutter", default=0,
                        help="Image gutter in pixels. Default: 0")
    parser.add_argument("-S", "--scaling", type=float, dest="scaling", default=1,
                        help="Image scale factor. Default: 1.0")
    parser.add_argument("-A", "--auth", dest="auth", default=None,
                        help="Authentication, user:password")
    parser.add_argument("-I", "--invert", action="store_true", dest="invert", default=False,
                        help="Invert axis order")

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    center = tuple(float(x) for x in args.center.split(","))
    auth = None if args.auth is None else tuple(args.auth.split(":"))
    version = tuple(int(x) for x in args.version.split("."))

    with setup_terminal():
        service = WMSService(args.url, args.layer, args.format, args.style, args.crs, version,
                             center, args.res, args.gutter, args.scaling, auth, args.invert)
        start_client(service)


if __name__ == "__main__":
    sys.exit(main())

