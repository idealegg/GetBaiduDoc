# -*- coding: utf-8 -*-
#!/usr/bin/env python

# contents_bdwk.py
from selenium import webdriver
from bs4 import BeautifulSoup

# ***selenium 自动操作网页***
options = webdriver.ChromeOptions()
options.add_argument('user-agent="Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36"')   #设置设备代理
driver = webdriver.Chrome(chrome_options=options)
driver.get('https://wenku.baidu.com/view/aa31a84bcf84b9d528ea7a2c.html')    #此处填写文章地址
page = driver.find_element_by_xpath("//div[@id='html-reader-go-more']")
driver.execute_script('arguments[0].scrollIntoView();', page)               #拖动网页到可见的元素去
nextpage = driver.find_element_by_xpath("//span[@class='moreBtn goBtn']")
nextpage.click()                                                            #进行点击下一页操作

# ***对打开的html进行分析***
html = driver.page_source
bf1 = BeautifulSoup(html.encode("utf8"), 'html.parser', from_encoding="utf8")

# 获得文章标题
title = bf1.find_all('h1', class_='reader_ab_test with-top-banner')
title = title.pop().find('span')
title = title.get_text()
if title:
  filename = title + '.txt'
else:
  filename = "doctmp.txt"

# 获得文章内容
texts_list = []
result = bf1.find_all('div', class_='ie-fix')
for each_result in result:
    texts = each_result.find_all('p')
    for each_text in texts:
        texts_list.append(each_text.string.encode('utf8'))

# ***保存为.txt文件
with open(filename, 'w') as f:
    f.writelines(texts_list)
    f.write('\n\n')