# -*- coding: utf8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

from setuptools import setup, find_packages

setup(
    name="MapsInTerminal",
    version="0.2",
    description="A WMS client for the terminal",
    author="Tommy Hellstrom",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pager",
        "Pillow",
        "img2txt.py"
    ],
    entry_points={
        "console_scripts": [
            "mapsint=mapsinterm.wms_client:main"
        ]
    }
)

