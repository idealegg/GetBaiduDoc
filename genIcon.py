#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import PythonMagick
img = PythonMagick.Image("free_doc.png")
img.sample('250x250')
img.write('free_doc.ico')