#!/usr/bin/python

import re,os,time,datetime,subprocess,sys,base64
import os.path
from shutil import copyfile
import requests
import json
import yaml
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



class RPA_Tools:

    def __init__(self):
        self.rpa = ''    
        self.RPA_LIST = dict()
        self.request_headers = dict()
        self.pw = 'secret'
        self.user = 'username'

    def get_groups(self,rpa):
        url = 'https://' + rpa  + '/fapi/rest/4_4/groups'
        j = self._get_request(url, self.request_headers)
        info = j['response']['context']
        return info


    def generate_headers(self,rpa):
        # Format the request header for REST calls.
        self.request_headers = {
                'Accept': 'application/json;format=1;prettyprint=1',
                'Username': self.user,
                'Password': self.pw
                }

    # Private Class function
    def _get_request(self, url, request_headers):
        r = requests.get(url, headers=request_headers, verify=False)
        if r.status_code != 200:
            logging.debug('Unexpected HTTP status-code ' + r.return_code + ' for URL=' + url)
            print("Bad status code, (" + r.status_code + ") for " + url)
        return r.json()



            
