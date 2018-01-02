# -*- coding: utf-8 -*-
# !/usr/bin/env python


import urllib2
import os
import sys
import HTMLParser


import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
import ssl


class MyAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)

s = requests.Session()
s.mount('https://', MyAdapter())



url = 'https://wkretype.bdimg.com/retype/zoom/b6cede1379563c1ec5da718b?pn=4&amp;o=jpg_6&amp;md5sum=0ddbf50525de711081575be83829370c&amp;sign=34311b7dd2&amp;png=6563-8405&amp;jpg=385586-535823'
hp = HTMLParser.HTMLParser()
url = hp.unescape(url)
print url
response = s.get(url)
data = response.content
