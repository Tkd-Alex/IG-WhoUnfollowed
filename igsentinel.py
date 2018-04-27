#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, pickle, json, os, random
from time import sleep, clock
from pprint import pprint
from fake_useragent import UserAgent

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
                 page_delay=25,
                 headless_browser=False,
                 nogui=False
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

        if not os.path.exists("cookies"):
            os.makedirs("cookies")

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

        self.browser = webdriver.Chrome(chromedriver_location, chrome_options=chrome_options)
        self.browser.implicitly_wait(self.page_delay)
        self.browser.set_page_load_timeout(self.page_delay)

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

        fwcounts = self.browser.find_element_by_xpath('//a[@href="/{}/followers/"]/span'.format(username))
        ActionChains(self.browser).move_to_element(fwcounts).click().perform()
        fwcounts = fwcounts.get_attribute("title")
        fwcounts = int(fwcounts.replace(",","").replace(".",""))
        print("Followers number for {}: {}".format(username, fwcounts))

        sleep(1)
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
                self.browser.execute_script("li = document.getElementsByClassName('_6e4x5'); li[li.length-{}].scrollIntoView()".format(random.randint(1,3)))
                
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

                # Humanize
                if iteration % 15 == 0:
                    self.browser.execute_script("li = document.getElementsByClassName('_6e4x5'); li[li.length-{}].scrollIntoView()".format(random.randint(5,14)))
                    sleep(1)

                # Humanize
                if iteration % 30 == 0:
                    sleep(random.randint(5,10))

                iteration += 1
                print("iteration={}, licounts={}, fast={}".format(iteration, licounts, trend['fast'] ))
                if iteration > predicted + random.randint(10,30):
                    break
                
                trend['counter'] += 1

                if licounts <= fwcounts:
                    break;
            except Exception as e:
                pass



