#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, pickle, json, os
from time import sleep
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
            
            print(l.content)
            
            if l.status_code == 200:
                jsonlogin = json.loads(l.content)
                if jsonlogin["authenticated"] is True:
                    cookies = l.headers['Set-Cookie']
                    sessionid = cookies.split("sessionid=")[1].split("; ")[0]
                    self.session.headers.update({"cookie": self.session.headers['cookie'] + " ; ds_user_id={} ; sessionid={}".format(jsonlogin["userId"], sessionid)})
                    pickle.dump(self.session, open("./sentinel", "wb"))
        else:
            self.session = pickle.load(open("./sentinel", "rb"))

    def checkpage(self, pagename):
        r = self.session.get("https://www.instagram.com/{}/".format(pagename))
        if r.status_code == 200:
            try:
                userinfo = r.text.split('<script type="text/javascript">window._sharedData = ')[1].split(';</script>')[0]
                userjson = json.loads(userinfo)
                private = userjson['entry_data']['ProfilePage'][0]['graphql']['user']['is_private']
                alreadyfollow = userjson['entry_data']['ProfilePage'][0]['graphql']['user']['followed_by_viewer'] 
                if alreadyfollow is True or private is False:
                    return "Ok, you will soon receive the notification", True
                else:
                    idpage = userjson['entry_data']['ProfilePage'][0]['graphql']['user']['id']
                    f = self.session.post('https://www.instagram.com/web/friendships/{}/follow/'.format(idpage))
                    print(f.content)
                    
                    if f.status_code == 200:
                        if f.json()['status'].lower() == 'ok':
                            return "You have a follow requests by {}. If you plan to continue, accept and try again. Else do not do anything".format(self.username), True
            except Exception as e:
                return "Sorry, there was an error. Try again", False
        else:
            return "Cannot find {} page".format(pagename), False

    def listfollowers(self, pageid):
        fwlist = []
        url = 'https://www.instagram.com/graphql/query/?query_hash=37479f2b8209594dde7facb0d904896a'
        f = self.session.get('{}&variables={}'.format(url, json.dumps({'id': pageid, 'first': 50}, separators=(',',':'))))
        if f.status_code == 200:
            fjson = f.json()
            if fjson['status'].lower() == 'ok':
                fwlist = fwlist + fjson['data']['user']['edge_followed_by']['edges']
            while fjson['data']['user']['edge_followed_by']['page_info']['has_next_page'] is True:
                sleep(1)
                end_cursor = fjson['data']['user']['edge_followed_by']['page_info']['end_cursor']
                f = self.session.get('{}&variables={}'.format(url, json.dumps({'id': pageid, 'first': 50, 'after': end_cursor}, separators=(',',':'))))
                if f.status_code == 200:
                    fjson = f.json()
                    if fjson['status'].lower() == 'ok':
                        fwlist = fwlist + fjson['data']['user']['edge_followed_by']['edges']
                else:
                    print("Failed with status code: {}".format(f.status_code))
                    print(f.content)
        else:
            print("Failed with status code: {}".format(f.status_code))
            print(f.content)