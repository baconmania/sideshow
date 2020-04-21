#!/usr/bin/env python

from setuptools import setup

setup(
  name='sideshow-client',
  version='1.0',
  author='Gowtam Lal',
  author_email='glal14@gmail.com',
  url='https://github.com/baconmania/sideshow',
  description='A client that runs on a Raspberry Pi and renders metrics to a framebuffer-backed display',
  install_requires=[
    "pygame",
    "requests"
  ],
)
