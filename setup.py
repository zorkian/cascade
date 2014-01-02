#!/usr/bin/env python

from distutils.core import setup

execfile('prodstate/version.py')

with open('requirements.txt') as requirements:
    required = requirements.read().splitlines()

kwargs = {
    "name": "prodstate",
    "version": str(__version__),
    "packages": ["prodstate"],
    "package_data": {"prodstate": ["plugins/*.py"]},
    "scripts": ["bin/prodstate"],
    "description": "Pluggable Distributed SSH Command Executer.",
    # PyPi, despite not parsing markdown, will prefer the README.md to the
    # standard README. Explicitly read it here.
    "long_description": open("README").read(),
    "author": "Mark Smith",
    "maintainer": "Mark Smith",
    "author_email": "mark@qq.is",
    "maintainer_email": "mark@qq.is",
    "license": "BSD",
    "install_requires": required,
    "url": "https://github.com/xb95/prodstate",
    "download_url": "https://github.com/xb95/prodstate/archive/master.tar.gz",
    "classifiers": [
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
}

setup(**kwargs)
