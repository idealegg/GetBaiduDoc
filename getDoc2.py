# -*- coding: utf-8 -*-
#!/usr/bin/env python

# contents_bdwk.py
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import os
import sys
import pprint
import time
import urllib2


count_class = "page-count"
input_class = "page-input"
title_class = "reader_ab_test with-top-banner"
text_class = 'ie-fix'
img_class = 'reader-pptstyle'

encodes = "utf8"
file_parser = 'html.parser'

page_pattern=re.compile("pageNo-\d+")


def init_driver():
  '''
  ***selenium 自动操作网页***
  #设置设备代理
  '''
  options = webdriver.ChromeOptions()
  options.add_argument('user-agent="Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36"') 
  return webdriver.Chrome(chrome_options=options)

def putUrl(driver, url):
  driver.get(url)    #此处填写文章地址
  
def display_all_doc(driver):
  '''
  #拖动网页到可见的元素去
  #click
  '''
  driver.execute_script('arguments[0].scrollIntoView();', 
                         driver.find_element_by_xpath("//div[@id='html-reader-go-more']"))               
  driver.find_element_by_xpath("//span[@class='moreBtn goBtn']").click()
  time.sleep(0.5)

def getBf(driver):
  '''
  # ***对打开的html进行分析***
  '''
  return BeautifulSoup(driver.page_source.encode(encodes), file_parser, from_encoding=encodes)

def getCount(bf):
  '''
  获取页数
  '''
  count_tags = bf.find_all('span', class_=count_class) # 'page-count'
  return int(count_tags.pop().get_text().split("/")[1])
  
def inputPage(driver, page):
  #print "inputPage: %d\n" % page
  page_input = driver.find_element_by_class_name(input_class)
  page_str = "%d" % page
  page_input.send_keys("".join([Keys.BACKSPACE * len(page_str), page_str, Keys.RETURN]))  
  time.sleep(0.5)

def getTitle(bf):
  '''
  获得文章标题
  '''
  titles = bf.find_all('h1', class_=title_class) # 'reader_ab_test with-top-banner'
  return titles.pop().find('span').get_text()

def getPages(bf, pageList, docType):
  pageNo = 0
  if docType ==  "text":
    pages = bf.find_all('div', class_=text_class) # 'ie-fix'
  elif docType ==  "img":
    pages = bf.find_all('img', class_=img_class) # 'reader-pptstyle'
  #print "pages: %d\n" % len(pages)
  for page in pages:
    pageNo = int(page.find_parents(id=page_pattern).pop().attrs['id'].split("-")[1])
    #print "pageNo: %d\n" % pageNo
    #print "pageList[pageNo-1]\n"
    #pprint.pprint(pageList[pageNo-1])
    if pageList[pageNo-1]:
      continue
    if docType ==  "text":
      texts_list = []
      texts = page.find_all('p')
      #print "texts: %d\n" % len(texts)
      for text in texts:
        texts_list.append(text.string.encode('utf8'))
      #print "texts_list: %d\n" % len(texts_list)
      pageList[pageNo-1] = texts_list
    elif docType ==  "img":
      pageList[pageNo-1] = page.attr('src')
  return pageList
  
def getDocType(bf):
  isText = bf.find_all('div', class_=text_class) # 'ie-fix'
  if len(isText):
    return "text"
  isImg = bf.find_all('div', class_=img_class) # 'reader-pptstyle'
  if len(isImg):
    return "img"
  return ""

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print "Usage: %s <url>\n" % os.path.basename(sys.argv[0])
    exit(1)
  # url = 'https://wenku.baidu.com/view/aa31a84bcf84b9d528ea7a2c.html'
  # url = 'https://wenku.baidu.com/view/590424de846a561252d380eb6294dd88d0d23d0b.html'
  driver = init_driver()
  putUrl(driver, sys.argv[1])
  display_all_doc(driver)
  bf = getBf(driver)
  docType = getDocType(bf)
  print "docType: %s\n" % docType
  if not docType:
    print "Unsupported doc type!\n"
    exit(2)
  count = getCount(bf)
  print "Pages: %d\n" % count
  title = getTitle(bf)
  print "title: %s\n" % title
  pageList = [0] * count
  it_range = range(1, count+1, 3)
  it_range.append(count)
  for i in it_range: 
    inputPage(driver, i)
    bf = getBf(driver)
    pageList = getPages(bf, pageList, docType)
  if title:
    filename = title + '.txt'
  else:
    filename = "doc_%d.txt" % os.getpid()
  f1 = open("tmp%d.log" % os.getpid(), 'w')
  f1.writelines(pprint.pformat(pageList))
  f1.write('\n\n')
  f1.close()
  
  if docType ==  "text":
    contents = []
    i = 1
    for page in pageList:
      if not page:
        print "This page [%d] could be an empty page or skipped just now!" % i
        print "Re open again.\n"
        inputPage(driver, i)
        bf = getBf(driver)
        pageList = getPages(bf, pageList)
        page = pageList[i-1]
      if not page:
        print "This page [%d] truly is an empty page.\n" % i
        page = []
      contents.extend(page)
      i = i + 1
    f = open(filename, 'w')
    f.writelines(contents)
    f.write('\n\n')
    f.close()
  elif docType ==  "img":
    #mkdir
    for page in pageList:
      request = urllib2.Request(url=page)
      response = urllib2.urlopen(request)
      data = response.read().decode('utf-8', 'replace')
      f = open('cat_500_600.jpg','wb')
      f.write(data)
      f.close()