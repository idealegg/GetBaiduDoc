#!/usr/bin/env python
#  -*- coding: utf-8 -*-


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import re
import os
import sys
import time
import StringIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from PIL import Image as image
import requests
import ConfigParser


class BaiduDoc:
  count_class = "page-count"
  count_class_ppt = "total-page"
  center_left = "centerLeft"
  ppt_class = 'mod ppt-mod'
  input_class = "page-input"
  input_class_ppt = "current-page"
  title_class = "reader_ab_test with-top-banner"
  text_class = 'ie-fix'
  img_class = 'reader-pptstyle'
  encodes = "utf8"
  file_parser = 'html.parser'
  page_pattern = re.compile("pageNo-\d+")
  supported_type = ('doc', 'pdf', 'ppt')

  def __init__(self, url):
    self.dcap = {}
    self.driver = None
    self.url = url
    self.bf = None
    self.pages = None
    # self.header = None
    self.title = ""
    self.doc_type = ""
    self.count = 0
    self.input_total_tag = None
    self.input_tag = None
    self.current_page = 1
    self.output = ""
    self.time = ""
    self.err_file = "err_%s.log" % self.get_time()
    self.tmp_file = ""
    self.config = { 'phantomjs': {}
                   , 'capabilities': dict(DesiredCapabilities.PHANTOMJS)
                   , 'webdriver' : { 'window_width' : '1124'
                                    ,'window_height' : '850'
                                    ,'scroll_timeout' : '0.5'
                                    ,'load_page_timeout' : '1.5'
                                    ,'https_verify' : 'false'}
                   , 'gen_pdf': { 'ratio' : '0.8'
                                 ,'quality' : '40'}}
    self.config['capabilities']["phantomjs.page.settings.userAgent"] = (
      "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36"
    )
    self.conf_parser = ConfigParser.ConfigParser()
    self.conf_file = "parameters.ini"

  def get_config(self):
    if os.path.isfile(self.conf_file):
      self.conf_parser.read(self.conf_file)
      if self.conf_parser.has_section('phantomjs'):
        self.config['phantomjs'].update(self.conf_parser.items('phantomjs'))
      elif self.conf_parser.has_section('webdriver'):
        self.config['capabilities'].update(self.conf_parser.items('capabilities'))
      elif self.conf_parser.has_section('webdriver'):
        self.config['webdriver'].update(self.conf_parser.items('webdriver'))
      elif self.conf_parser.has_section('gen_pdf'):
        self.config['gen_pdf'].update(self.conf_parser.items('gen_pdf'))

  def get_time(self):
    self.time = time.strftime("%Y%m%d_%H%M%S")
    return self.time

  def init_driver(self, load_images=False):
    '''
    ***selenium 自动操作网页***
    #设置设备代理
    '''
    self.config['phantomjs']['load-images'] = 'true' if load_images else 'false'
    self.config['phantomjs']['disk-cache'] = 'true'
    service_args = map(lambda x: ''.join(["--", str(x), "=", self.config['phantomjs'][x]]),
                       self.config['phantomjs'].keys())
    self.driver = webdriver.PhantomJS(executable_path='phantomjs\\phantomjs.exe',
                               service_args=service_args,
                               desired_capabilities=self.config['capabilities'])  # 加载网址

  def put_url(self):
    self.driver.set_window_size( int(self.config['webdriver']['window_width'])
                                ,int(self.config['webdriver']['window_height']))
    print "Loading page..."
    self.driver.get(self.url)    #此处填写文章地址
    print "Loaded page..."

  def display_all_doc(self):
    '''
    #拖动网页到可见的元素去
    #click
    '''
    self.driver.execute_script('arguments[0].scrollIntoView();',
                               self.driver.find_element_by_xpath("//div[@id='html-reader-go-more']"))
    self.driver.find_element_by_xpath("//span[@class='moreBtn goBtn']").click()
    time.sleep(float(self.config['webdriver']['scroll_timeout']))

  def get_bf(self):
    '''
    # ***对打开的html进行分析***
    '''
    self.bf = BeautifulSoup(self.driver.page_source.encode(self.encodes),
                         self.file_parser, 
                         from_encoding=self.encodes)

  def get_count(self):
    '''
    获取页数
    # 'page-count'/'total-page'
    '''
    count_tags = self.bf.find_all('span', 
                                  class_=self.count_class if self.doc_type != "ppt" else self.count_class_ppt)
    self.count = int(count_tags.pop().get_text().split("/")[1])

  def choose_page(self, page):
    '''
    # 'page-input'/'current-page'
    '''
    self.input_total_tag = self.driver.find_element_by_class_name(self.center_left)
    try:
      self.input_tag = self.input_total_tag.find_element_by_class_name(self.input_class)
    except NoSuchElementException:
      self.input_tag = self.input_total_tag.find_element_by_class_name(self.input_class_ppt)
    page_str = "%d" % page
    self.input_tag.clear()
    if self.input_tag.get_attribute('value'):
      self.input_tag.clear()
    self.input_tag.send_keys("".join([page_str, Keys.ENTER]))
    self.current_page = page
    time.sleep(float(self.config['webdriver']['load_page_timeout']))

  def getTitle(self):
    '''
    获得文章标题
    '''
    header = self.bf.find('h1', class_=self.title_class) # 'reader_ab_test with-top-banner'
    self.title = header.find('span').get_text()
    self.doc_type = header.find('b').attrs['class'][1].split('-')[1]

  def get_pages(self):
    pages = None
    if self.doc_type == "doc":
      pages = self.bf.find_all('div', class_=self.text_class) # 'ie-fix'
    elif self.doc_type == "pdf":
      pages = self.bf.find_all('img', class_=self.img_class) # 'reader-pptstyle'
    elif self.doc_type == "ppt":
      mod_class = self.bf.find('div', class_=self.ppt_class) # 'mod ppt-mod'
      print "Analysing page No.: %d/%d" % (self.current_page, self.count)
      self.pages[self.current_page - 1] = mod_class.find('img').attrs['src']
      return
    for page in pages:
      page_no = int(page.find_parents(id=self.page_pattern).pop().attrs['id'].split("-")[1])
      print "Analysing page No.: %d/%d" % (page_no, self.count)
      if self.pages[page_no-1]:
        continue
      if self.doc_type == "doc":
        texts_list = []
        texts = page.find_all('p')
        for text in texts:
          texts_list.append(text.string.encode('utf8'))
        self.pages[page_no-1] = texts_list
      elif self.doc_type == "pdf":
        self.pages[page_no-1] = page.attrs['src']

  def getUrlData(self, url):
    is_https = url.lower().startswith('https')
    fe = None
    save_stderr = None
    if is_https:
      fe = open(self.err_file, "w+")
      save_stderr = sys.stderr
      sys.stderr = fe
    response = requests.get(url, verify=self.config['webdriver']['https_verify'].lower() != 'false')
    if is_https:
      sys.stderr = save_stderr
      fe.flush()
      fe.seek(0)
      err_info = fe.readline()
      fe.close()
      if not err_info or err_info.find('InsecureRequestWarning: Unverified HTTPS request is being made') == -1:
        print err_info
    response.close()
    return response.content

  def main(self):
    self.init_driver()
    self.put_url()
    self.get_bf()
    self.getTitle()
    print "title: %s" % self.title
    print "doc_type: %s" % self.doc_type
    if self.doc_type not in self.supported_type:
      raise Exception("Unsupported doc type!")
    if self.doc_type in self.supported_type[:-1]:
      self.display_all_doc()
    elif self.doc_type == "ppt":
      print "Reopening browser"
      self.driver.close()
      self.driver.quit()
      self.init_driver(True)
      self.put_url()
      self.get_bf()
    self.get_count()
    print "Pages: %d" % self.count
    self.pages = [None] * self.count
    if self.doc_type != "ppt":
      it_range = range(1, self.count+1, 3)
      it_range.append(self.count)
    else:
      it_range = range(1, self.count+1)
    for i in it_range:
      self.choose_page(i)
      self.get_bf()
      self.get_pages()
    if self.title:
      self.output = self.title + '.txt'
    else:
      self.output = "doc_%s.txt" % self.get_time()
    if self.doc_type == "doc":
      contents = []
      i = 1
      for page in self.pages:
        print "Assembling %d/%d" %(i, self.count)
        if not page:
          print "This page [%d] may be an empty page or skipped just now!" % i
          print "Re open again."
          self.choose_page(i)
          self.get_bf()
          self.get_pages()
          page = self.pages[i-1]
        if not page:
          print "This page [%d] truly is an empty page." % i
          page = []
        contents.extend(page)
        i += 1
      f = open(self.output, 'w')
      f.writelines(contents)
      f.write('\n\n')
      f.close()
      return self.output
    elif self.doc_type in self.supported_type[1:]:
      ratio = float(self.config['gen_pdf']['ratio'])
      quality = int(self.config['gen_pdf']['quality'])
      if self.title:
        self.output = self.title + '.pdf'
      else:
        self.output = "%s_%s.pdf" % (self.doc_type, self.get_time())
      (w, h) = landscape(A4)
      c = canvas.Canvas(self.output, pagesize = landscape(A4))
      i = 1
      for page in self.pages:
        print "Assembling %d/%d" % (i, self.count)
        if not page:
          print "This page [%d] may be skipped just now!" % i
          print "Re open again."
          self.choose_page(i)
          self.get_bf()
          self.get_pages()
          page = self.pages[i-1]
        if not page:
          print "This page [%d] truly is lost." % i
        else:
          data = self.getUrlData(page)
          im=image.open(StringIO.StringIO(data))
          (ori_w,ori_h) = im.size
          im1 = im.resize((int(ori_w * ratio), int(ori_h * ratio)), image.ANTIALIAS)
          # here the file name should be different each time.
          # or the same picture would be drawn
          self.tmp_file = "tmp_%s_%d.jpg" % (self.get_time(), i)
          im1.save(self.tmp_file, format="jpeg", quality=quality, optimize=True)
          c.drawImage(self.tmp_file, 0, 0, w, h)
          os.remove(self.tmp_file)
          c.showPage()
          im.close()
          im1.close()
        i += 1
      c.save()
      return self.output

  def finalize(self):
    self.driver.quit()
    if os.path.isfile(self.err_file):
      os.remove(self.err_file)


if __name__ == "__main__":
  if len(sys.argv) != 1:
    print "Usage: %s" % os.path.basename(sys.argv[0])
    exit(1)
  success = True
  print "Please input the URL:"
  url = sys.stdin.readline()
  url = url[:-1]
  # url = 'https://wenku.baidu.com/view/aa31a84bcf84b9d528ea7a2c.html'  # doc
  # url = 'https://wenku.baidu.com/view/590424de846a561252d380eb6294dd88d0d23d0b.html'  # pdf
  # url = 'https://wenku.baidu.com/view/a6d77180bcd126fff7050bff.html'  # ppt
  print "Opening browser..."
  baidu_doc = BaiduDoc(url)
  try:
    baidu_doc.main()
  except:
    success = False
    raise
  finally:
    baidu_doc.finalize()
    print "Get Baidu Doc '%s' %s!\n" %(baidu_doc.output, "successfully" if success else "failed")
    os.system("pause")
