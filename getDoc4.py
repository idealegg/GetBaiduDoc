#!/usr/bin/env python
#  -*- coding: utf-8 -*-


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import re
import os
import sys
import pprint
import time
import urllib2
import StringIO
#import HTMLParser
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from PIL import Image as image
import requests
from requests.adapters import HTTPAdapter
import ssl


count_class = "page-count"
count_class_ppt = "total-page'"
input_class = "page-input"
input_class_ppt = "current-page"
title_class = "reader_ab_test with-top-banner"
text_class = 'ie-fix'
img_class = 'reader-pptstyle'

encodes = "utf8"
file_parser = 'html.parser'

page_pattern = re.compile("pageNo-\d+")

supported_type = (doc, pdf, ppt)

def init_driver():
  '''
  ***selenium 自动操作网页***
  #设置设备代理
  '''
  dcap = dict(DesiredCapabilities.PHANTOMJS)  # 设置userAgent
  dcap["phantomjs.page.settings.userAgent"] = (
  #"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0"
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36"
  )
  return webdriver.PhantomJS(executable_path='phantomjs-2.1.1-windows\\bin\\phantomjs.exe',
                             service_args=['--load-images=false',
                                           '--disk-cache=true'],
                             desired_capabilities=dcap)  # 加载网址
  #options = webdriver.ChromeOptions()
  #options.add_argument('user-agent="Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36"')
  #return webdriver.Chrome(chrome_options=options)


def putUrl(driver, url):
  driver.set_window_size(1124, 850)
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


def getCount(bf, dtype):
  '''
  获取页数
  # 'page-count'/'total-page'
  '''
  count_tags = bf.find_all('span', class_=count_class if dtype != "ppt" else count_class_ppt)
  return int(count_tags.pop().get_text().split("/")[1])


def inputPage(driver, page):
  '''
  # 'page-input'/'current-page'
  '''
  #print "inputPage: %d\n" %page
  page_input = driver.find_element_by_class_name(input_class)
  page_str = "%d" % page
  page_input.send_keys("".join([Keys.BACKSPACE * len(page_str), page_str, Keys.ENTER]))
  time.sleep(1.5)


def getTitle(bf):
  '''
  获得文章标题
  '''
  titles = bf.find_all('h1', class_=title_class) # 'reader_ab_test with-top-banner'
  title = titles.index[0].find('span').get_text()
  dtype = titles.index[0].find('b').attrs['class'].split('-')[1]
  return title, dtype


def getPages(bf, pageList, docType, count):
  pageNo = 0
  if docType ==  "text":
    pages = bf.find_all('div', class_=text_class) # 'ie-fix'
  elif docType ==  "img":
    pages = bf.find_all('img', class_=img_class) # 'reader-pptstyle'
  #print "pages: %d\n" % len(pages)
  for page in pages:
    pageNo = int(page.find_parents(id=page_pattern).pop().attrs['id'].split("-")[1])
    print "Analysing pageNo: %d/%d\n" % (pageNo, count)
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
      pageList[pageNo-1] = page.attrs['src']
  return pageList

def getUrlData(url):
  ishttp = url.lower().startswith('https')
  fe = None
  save_stderr = None
  if ishttp:
    fe = open("err.log_%d" % os.getpid(), "w+")
    save_stderr = sys.stderr
    sys.stderr = fe
  response = requests.get(url, verify=False)
  if ishttp:
    sys.stderr = save_stderr
    fe.flush()
    fe.seek(0)
    err_info = fe.readline()
    fe.close()
    if not err_info or err_info.find('InsecureRequestWarning: Unverified HTTPS request is being made') == -1:
      print err_info
  response.close()
  return  response.content


def main(driver, url):
  putUrl(driver, url)
  bf = getBf(driver)
  title, docType = getTitle(bf)
  print "title: %s\n" % title
  print "docType: %s\n" % docType
  if not docType in supported_type:
    raise Exception( "Unsupported doc type!")
  if docType in supported_type[:-1]:
    display_all_doc(driver)
  count = getCount(bf)
  print "Pages: %d\n" % count

  pageList = [0] * count
  it_range = range(1, count+1, 3)
  it_range.append(count)
  for i in it_range:
    inputPage(driver, i)
    bf = getBf(driver)
    pageList = getPages(bf, pageList, docType, count)
  if title:
    filename = title + '.txt'
  else:
    filename = "doc_%d.txt" % os.getpid()
  #f1 = open("tmp%d.log" % os.getpid(), 'w')
  #f1.writelines(pprint.pformat(pageList))
  #f1.write('\n\n')
  #f1.close()

  if docType ==  "text":
    contents = []
    i = 1
    for page in pageList:
      print "Assembling %d/%d\n" %(i, count)
      if not page:
        print "This page [%d] could be an empty page or skipped just now!" % i
        print "Re open again.\n"
        inputPage(driver, i)
        bf = getBf(driver)
        pageList = getPages(bf, pageList, docType, count)
        page = pageList[i-1]
      if not page:
        print "This page [%d] truly is an empty page.\n" % i
        page = []
      contents.extend(page)
      i += 1
    f = open(filename, 'w')
    f.writelines(contents)
    f.write('\n\n')
    f.close()
    return filename
  elif docType ==  "img":
    ratio = 1.2
    quality = 40
    #hp = HTMLParser.HTMLParser()
    if title:
      f_pdf = title + '.pdf'
    else:
      f_pdf = "ppt%d.pdf" % os.getpid()
    (w, h) = landscape(A4)
    c = canvas.Canvas(f_pdf, pagesize = landscape(A4))
    i = 1
    for page in pageList:
      print "Assembling %d/%d\n" % (i, count)
      if not page:
        print "This page [%d] could be skipped just now!" % i
        print "Re open again.\n"
        inputPage(driver, i)
        bf = getBf(driver)
        pageList = getPages(bf, pageList, docType, count)
        page = pageList[i-1]
      if not page:
        print "This page [%d] truly is lost.\n" % i
        page = ""
      else:
        #url = hp.unescape(url)
        data = getUrlData(page)
        im=image.open(StringIO.StringIO(data))
        (ori_w,ori_h) = im.size
        im1 = im.resize((int(ori_w/ratio), int(ori_h/ratio)), image.ANTIALIAS)
        tmpf = "tmp%d_%d.jpg" % (os.getpid(), i)
        im1.save(tmpf, format="jpeg", quality=quality, optimize=True)
        c.drawImage(tmpf, 0, 0, w, h)
        os.remove(tmpf)
        c.showPage()
        im.close()
        im1.close()
      i = i + 1
    c.save()
    return f_pdf

if __name__ == "__main__":
  #if len(sys.argv) != 2:
  #  print "Usage: %s <url>\n" % os.path.basename(sys.argv[0])
  #  exit(1)
  success = True
  print "Please input the URL:\n"
  url = sys.stdin.readline()
  url = url[:-1]
  docname = ""
  # url = 'https://wenku.baidu.com/view/aa31a84bcf84b9d528ea7a2c.html'
  # url = 'https://wenku.baidu.com/view/590424de846a561252d380eb6294dd88d0d23d0b.html'
  driver = init_driver()
  try:
    #main(driver, sys.argv[1])
    docname = main(driver, url)
  except Exception, e:
    success = False
    raise
  finally:
    driver.quit()#
    errfile = "err.log_%d" % os.getpid()
    if os.path.isfile(errfile):
      os.remove(errfile)
    print "Get Baidu Doc '%s' %s!\n" %(docname, "successfully" if success else "failed")
    os.system("pause")
