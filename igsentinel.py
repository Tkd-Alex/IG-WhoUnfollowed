#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests, pickle, json, os, random
from time import sleep, clock
from pprint import pprint
from fake_useragent import UserAgent
from datetime import datetime
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException

class Sentinel:
    def __init__(self, username, password, 
                 proxy=None,
                 page_delay=20,
                 headless_browser=False,
                 nogui=False,
                 mobile=False
                ):
        self.username = username
        self.password = password
        
        if nogui:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        self.browser = None
        self.headless_browser = headless_browser
        self.proxy = proxy

        self.nogui = nogui

        self.page_delay = page_delay
        self.switch_language = True

        self.mobile = mobile

        self.initselenium()

    def initselenium(self):
        chromedriver_location = './chromedriver'
        chrome_options = Options()
        chrome_options.add_argument('--dns-prefetch-disable')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument('--disable-setuid-sandbox')

        chrome_options.add_argument('--disable-gpu')

        if not self.proxy is None:
            proxy = self.proxy.split(":")
            chrome_options.add_argument('--proxy-server={}:{}'.format(proxy[0], proxy[1]))

        if self.headless_browser:
            chrome_options.add_argument('--headless')

        chrome_prefs = {
            'intl.accept_languages': 'en-US',
            'profile.managed_default_content_settings.images': 2,
            'popups': 1
        }
        chrome_options.add_experimental_option('prefs', chrome_prefs)

        if self.mobile:
            mobile_emulation = { "deviceName": "Nexus 5" }
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

        self.browser = webdriver.Chrome(chromedriver_location, chrome_options=chrome_options)
        self.browser.implicitly_wait(self.page_delay)

        return self

    def login(self):

        self.browser.get('https://www.instagram.com')
        cookie_loaded = False

        try:
            if os.path.isfile('sentinel.pkl'):
                self.browser.get('https://www.google.com')
                for cookie in pickle.load(open('sentinel.pkl', 'rb')):
                    self.browser.add_cookie(cookie)
                    cookie_loaded = True
        except (WebDriverException, OSError, IOError):
            print("Cookie file not found, creating cookie...")

        self.browser.get('https://www.instagram.com')
        login_elem = self.browser.find_elements_by_xpath("//*[contains(text(), 'Log in')]")
        
        if len(login_elem) == 0 and cookie_loaded is True:
            return True

        if self.switch_language:
            try:
                self.browser.find_element_by_xpath("//select[@class='_fsoey']/option[text()='English']").click()
            except Exception as e:
                pass

        login_elem = self.browser.find_element_by_xpath("//article/div/div/p/a[text()='Log in']")
        if login_elem is not None:
            ActionChains(self.browser).move_to_element(login_elem).click().perform()

        input_username = self.browser.find_elements_by_xpath("//input[@name='username']")
        ActionChains(self.browser).move_to_element(input_username[0]).click().send_keys(self.username).perform()
        sleep(1)

        input_password = self.browser.find_elements_by_xpath("//input[@name='password']")
        ActionChains(self.browser).move_to_element(input_password[0]).click().send_keys(self.password).perform()

        login_button = self.browser.find_element_by_xpath("//form/span/button[text()='Log in']")
        ActionChains(self.browser).move_to_element(login_button).click().perform()
        sleep(2)

        nav = self.browser.find_elements_by_xpath('//nav')
        if len(nav) == 2:
            pickle.dump(self.browser.get_cookies(), open('sentinel.pkl', 'wb'))
            return True
        
        return False

    def end(self):
        self.browser.delete_all_cookies()
        self.browser.quit()

        if self.nogui:
            self.display.stop()

        return self

    def checkuser(self, username):
        self.browser.get('https://www.instagram.com/{}'.format(username))
        try:
            error = self.browser.find_element_by_class_name("error-container")
            if 'isn\'t available' in error.text.lower():
                return False, error.text
        except NoSuchElementException:
            pass
        try:
            isprivate = self.browser.find_element_by_xpath("//h2[@class='_kcrwx']")
            if 'private' in isprivate.text.lower():
                try:
                    follow_button = self.browser.find_element_by_xpath("//button[text()='Follow']")
                    ActionChains(self.browser).move_to_element(follow_button).click().perform()
                    return False, "You have a follow requests by from selenium.webdriver.common.action_chains import ActionChains{}. If you plan to continue, accept and try again. Else do not do anything".format(self.username)
                except NoSuchElementException:
                    return False, "It would seem that yours is private. We tried to follow you but without any success."
        except NoSuchElementException:
            pass
        return True, "Ok, you will soon receive the notification"

    def listfollowers(self, username):
        self.browser.get('https://www.instagram.com/{}'.format(username))
        sleep(1)

        # Get the followers count
        fwcounts = self.browser.find_element_by_xpath('//a[@href="/{}/followers/"]/span'.format(username))
        ActionChains(self.browser).move_to_element(fwcounts).click().perform()
        fwcounts = fwcounts.get_attribute("title")
        fwcounts = int(fwcounts.replace(",","").replace(".",""))

        sleep(1)
        # Init support variable.
        # li counts = numbers of followers founded.
        # iteration = numbers of iteration.
        # fast = numbers of scrolling to do fast.
        # slow = numbers of scrolling to do slow.
        # tren = counter, numbers of iteration. fast, boolean fast or slow.
        # predicted = numbers of predicted iteration.
        licounts = 0
        iteration = 0
        fast = random.randint(5,8)
        slow = random.randint(9,15)
        trend = {
            'counter': 0,
            'fast': True
        }
        predicted = fwcounts/12
        while(True):
            try:
                random.seed(clock)

                # Scrolling humanized, go to the n last element and after +1.
                i = random.randint(2, 10)
                while True:
                    sleep(0.2)
                    self.browser.execute_script("li = document.getElementsByClassName('_6e4x5'); li[li.length-{}].scrollIntoView()".format(i))
                    i = i-1
                    if i == 1:
                        break
                
                # Humanize
                if trend['fast'] is True and trend['counter'] <= fast:
                    sleep(random.uniform(0.2, 0.9))
                elif trend['fast'] is True and trend['counter'] > fast:
                    trend['counter'] = 0
                    trend['fast'] = False
                
                if trend['fast'] is False and trend['counter'] <= slow:
                    sleep(random.randint(2,5))
                elif trend['fast'] is False and trend['counter'] > slow:
                    trend['counter'] = 0
                    trend['fast'] = True

                li = self.browser.find_elements_by_xpath("//li[@class='_6e4x5']")
                licounts = len(li)

                # Humanize. Scroll to middle, wait and exit.
                if iteration % 10 == 0 and iteration != 0:
                    print("datetime={}, account={}, iteration={}, humanize=scroll back".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), username, iteration))
                    self.browser.execute_script("li = document.getElementsByClassName('_6e4x5'); li[li.length/2].scrollIntoView()")
                    sleep(1)

                    print("datetime={}, account={}, iteration={}, humanize=exit and wait".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), username, iteration))
                    exitbtn = self.browser.find_element_by_xpath("//button[@class='_dcj9f']")
                    ActionChains(self.browser).move_to_element(exitbtn).click().perform()
                    sleep(1)
                    showfw = self.browser.find_element_by_xpath('//a[@href="/{}/followers/"]/span'.format(username))
                    ActionChains(self.browser).move_to_element(showfw).click().perform()

                    sleep(random.randint(5,10))

                iteration += 1
                trend['counter'] += 1
                
                if licounts >= fwcounts or iteration > predicted + random.randint(10,30):
                    break

                print("datetime={}, account={}, iteration={}, licounts={}, fast={}".format(datetime.now().strftime('%Y/%m/%d %H:%M:%S'), username, iteration, licounts, trend['fast'] ))
                
            except Exception as e:
                pass

        fwlist = []
        if licounts >= fwcounts:
            for fw in li:
                splittedtext = fw.text.split("\n")
                fwlist.append(splittedtext[0])

        return fwlist


