#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import pickle
import json
import os
import random
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus
from pprint import pprint
from pyvirtualdisplay import Display

from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s]: %(message)s", datefmt="%d/%m/%Y %H:%M:%S", level=logging.INFO)


class Sentinel:
    def __init__(
        self,
        username,
        password,
        proxy=None,
        headless_browser=False,
        nogui=False,
        mobile=False,
        implicitly_wait=15,
        set_page_load_timeout=120,
    ):
        self.logger = logging.getLogger("SENTINEL")

        self.username = username
        self.password = password

        if nogui is True and headless_browser is False:
            self.display = Display(visible=0, size=(1280, 800))
            self.display.start()

        self.browser = None
        self.headless_browser = headless_browser
        self.proxy = proxy

        self.nogui = nogui

        self.implicitly_wait = implicitly_wait
        self.set_page_load_timeout = set_page_load_timeout

        self.mobile = mobile
        self.init_selenium()

    def init_selenium(self):
        chromedriver_location = "./chromedriver"
        chrome_options = Options()
        for arg in [
            "--dns-prefetch-disable",
            "--no-sandbox",
            "--lang=en-US",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disable-notifications",
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
        ]:
            chrome_options.add_argument(arg)

        if not self.proxy is None:
            proxy = self.proxy.split(":")
            chrome_options.add_argument("--proxy-server={}:{}".format(proxy[0], proxy[1]))

        if self.headless_browser:
            chrome_options.add_argument("--headless")

        chrome_prefs = {"intl.accept_languages": "en-US", "profile.managed_default_content_settings.images": 2, "popups": 1}
        chrome_options.add_experimental_option("prefs", chrome_prefs)

        if self.mobile:
            mobile_emulation = {"deviceName": "Nexus 5"}
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

        self.browser = webdriver.Chrome(chromedriver_location, chrome_options=chrome_options)

        self.browser.implicitly_wait(self.implicitly_wait)
        self.browser.set_page_load_timeout(self.set_page_load_timeout)

        return self

    def login(self):

        self.browser.get("https://www.instagram.com")
        self.accept_cookie()
        cookie_loaded = False

        try:
            if os.path.isfile("sentinel.pkl") is True:
                # self.browser.get('https://www.google.com')
                for cookie in pickle.load(open("sentinel.pkl", "rb")):
                    self.browser.add_cookie(cookie)
                    cookie_loaded = True
            else:
                self.logger.info("Cookie file not found, creating cookie...")
        except (WebDriverException, OSError, IOError):
            self.logger.info("Cookie file not found, creating cookie...")

        if cookie_loaded is True:
            self.browser.get("https://www.instagram.com")
            self.accept_cookie()

        nav_counter = len(self.browser.find_elements_by_xpath("//nav"))
        if nav_counter == 2:
            pickle.dump(self.browser.get_cookies(), open("sentinel.pkl", "wb"))
            return True

        self.browser.get("https://www.instagram.com/accounts/login/?source=auth_switcher")

        input_username = self.browser.find_element_by_xpath("//input[@name='username']")
        ActionChains(self.browser).move_to_element(input_username).click().send_keys(self.username).perform()
        self.logger.info("Write username: {}".format(self.username))
        time.sleep(0.2)

        input_password = self.browser.find_element_by_xpath("//input[@name='password']")
        ActionChains(self.browser).move_to_element(input_password).click().send_keys(self.password).perform()
        self.logger.info("Write password: {}".format(self.password))
        time.sleep(0.2)

        login_button = self.browser.find_element_by_xpath("//button[@type='submit']")
        ActionChains(self.browser).move_to_element(login_button).click().perform()
        self.logger.info("Click 'Log in' button ... ")
        time.sleep(2)

        self.accept_cookie()
        nav_counter = len(self.browser.find_elements_by_xpath("//nav"))
        if nav_counter == 2:
            pickle.dump(self.browser.get_cookies(), open("sentinel.pkl", "wb"))
            return True

        return False

    def end(self):
        self.browser.delete_all_cookies()
        self.browser.quit()

        if self.nogui:
            self.display.stop()

        return self

    def checkuser(self, username):
        self.browser.get("https://www.instagram.com/{}".format(username))
        try:
            error = self.browser.find_element_by_class_name("error-container")
            if "isn't available" in error.text.lower():
                return False, error.text
        except NoSuchElementException:
            pass
        try:
            isprivate = self.browser.find_element_by_xpath("//h2[@class='_kcrwx']")
            if "private" in isprivate.text.lower():
                try:
                    follow_button = self.browser.find_element_by_xpath("//button[text()='Follow']")
                    ActionChains(self.browser).move_to_element(follow_button).click().perform()
                    return (
                        False,
                        "You have a follow requests by from selenium.webdriver.common.action_chains import ActionChains{}. If you plan to continue, accept and try again. Else do not do anything".format(
                            self.username
                        ),
                    )
                except NoSuchElementException:
                    return False, "It would seem that yours is private. We tried to follow you but without any success."
        except NoSuchElementException:
            pass
        return True, "Ok, you will soon receive the notification"

    def listfollowers(self, username):
        followers_list = []

        self.browser.get("view-source:https://www.instagram.com/{}?__a=1".format(username))
        soup = BeautifulSoup(self.browser.page_source, features="html.parser")
        data = json.loads(soup.text)

        profile_data = data["graphql"]["user"]
        data = {
            "id": profile_data["id"],
            "include_reel": False,
            "first": 50,
            "after": "",
        }
        has_next = True
        iteration = 0
        while has_next:
            self.browser.get(
                "view-source:https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a&{}".format(urlencode(data, quote_via=quote_plus))
            )
            soup = BeautifulSoup(self.browser.page_source, features="html.parser")
            followers_data = json.loads(soup.text)
            has_next = followers_data["data"]["user"]["edge_followed_by"]["page_info"]["has_next_page"]
            data.update({"after": followers_data["data"]["user"]["edge_followed_by"]["page_info"]["end_cursor"]})
            followers_list += [item["node"]["username"] for item in followers_data["data"]["user"]["edge_followed_by"]["edges"]]
            self.logger.info(
                "#{} - {} ({}), Followers: {}/{}, Page: {}".format(
                    str(iteration).zfill(len(str(profile_data["edge_followed_by"]["count"] // 50))),
                    username,
                    profile_data["id"],
                    str(len(followers_list)).zfill(len(str(profile_data["edge_followed_by"]["count"]))),
                    profile_data["edge_followed_by"]["count"],
                    data["after"],
                )
            )
            iteration += 1
            time.sleep(5 if iteration % 5 == 0 else random.uniform(0.2, 0.8))
        return followers_list

    def accept_cookie(self):
        time.sleep(0.5)
        try:
            self.browser.find_element_by_xpath("//button[contains(., 'Accept')]").click()
            self.logger.info("Succefully click on 'Accept' button")
            return True
        except (NoSuchElementException, StaleElementReferenceException):
            self.logger.error("Unable to find button with 'Accept' text. Skip.")
            return False
