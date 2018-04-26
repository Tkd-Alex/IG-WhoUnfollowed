#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, pickle, json, os
from pprint import pprint
from fake_useragent import UserAgent

class Sentinel:
    def __init__(self, username, password, proxy=None):
        self.username = username
        self.password = password
        self.session = requests.Session()
        if not proxy is None:
            proxies = { 'http': 'http://{}'.format(proxy), 'https': 'http://{}'.format(proxy) }
            self.session.proxies.update(proxies)          

    def login(self):
        if not os.path.exists("./sentinel"):
            ua = UserAgent()
            useragent = ua.random
            headers = { 'User-Agent': useragent }
            r = self.session.get("https://instagram.com", headers=headers)
            self.session.headers.update({
                'origin': 'https://www.instagram.com',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                'x-requested-with': 'XMLHttpRequest',
                'user-agent': useragent,
                'cookie': 'rur={}; csrftoken={}; mid=WuI2OQAEAAGriWx5lB4XD2pCeCtX'.format(r.cookies['rur'], r.cookies['csrftoken']),
                'x-csrftoken': '{}'.format(r.cookies['csrftoken']),
                'x-instagram-ajax': '1',
                'content-type': 'application/x-www-form-urlencoded',
                'accept': '*/*',
                'referer': 'https://www.instagram.com/',
                'authority': 'www.instagram.com',
            })
            l = self.session.post(
                "https://www.instagram.com/accounts/login/ajax/", 
                data={'username': self.username, 'password': self.password, 'queryParams': {}}, 
                allow_redirects=True)
            if l.status_code == 200:
                if l.text.find(self.username) != -1:
                    pickle.dump(self.session, open("./sentinel", "wb"))
        else:
            self.session = pickle.load(open("./sentinel", "rb"))