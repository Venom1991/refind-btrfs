# region Licensing
# SPDX-FileCopyrightText: 2020 Luka Žaja <luka.zaja@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

""" refind-btrfs - Generate rEFInd manual boot stanzas from Btrfs snapshots
Copyright (C) 2020  Luka Žaja

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# endregion

import setuptools

with open("README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

setuptools.setup(
    name="refind-btrfs",
    version="0.3.9",
    author="Luka Žaja",
    author_email="luka.zaja@protonmail.com",
    description="Generate rEFInd manual boot stanzas from Btrfs snapshots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="rEFInd, btrfs",
    url="https://github.com/Venom1991/refind-btrfs",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Boot",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "antlr4-python3-runtime",
        "injector",
        "more-itertools",
        "pid",
        "semantic-version",
        "systemd-python",
        "tomlkit",
        "transitions",
        "typeguard",
        "watchdog",
    ],
    entry_points={
        "console_scripts": [
            "refind-btrfs=refind_btrfs:main",
        ],
    },
    python_requires=">=3.9",
)
