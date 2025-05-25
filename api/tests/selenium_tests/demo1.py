# /usr/bin/bash python
# -*- coding:utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
options = webdriver.ChromeOptions()
# 隐藏"Chrome正在受到自动软件的控制"
options.add_experimental_option('useAutomationExtension', False)  # 去掉开发者警告
options.add_experimental_option('excludeSwitches', ['enable-automation'])

options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(executable_path='../../datas/servers/chromedriver', options=options)

driver.get("https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&tn=baidu&wd=%E5%A5%B3%E7%A5%9E%E8%8A%82%E5%BF%AB%E4%B9%90&oq=iPad%25E7%2594%25BB%25E6%25B0%25B4%25E5%25BD%25A9&rsv_pq=da863c960031fa89&rsv_t=320bU5S7GOOB43J2GLgjE66RWcLR2giCuNktmA5I6Wm7VcW7dZ1It2hKWxs&rqlang=cn&rsv_enter=1&rsv_dl=tb&inputT=8595&rsv_sug3=16&rsv_sug1=14&rsv_sug7=101&rsv_sug2=0&rsv_sug4=11686")
content = driver.title.split("_")[0]
print(content)
driver.close()
