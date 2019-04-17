#!/usr/bin/python

import re,os,time,datetime,subprocess,sys,base64
import os.path
from shutil import copyfile
import requests
import json
import yaml
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging

class VPLEX_Tools:

    def __init__(self):
        self.vplex = ''    
        self.VPLEX_LIST = dict()
        self.request_headers = dict()
        with open('/usr/local/StorageOps/etc/config.yaml') as info:
            self.VPLEX_LIST = yaml.load(info)


    def get_views(self,vplex,cluster):
        url = 'https://' + vplex  + '/vplex/clusters/' + cluster + '/exports/storage-views/*'
        j = self._get_request(url, self.request_headers)
        info = j['response']['context']
        return info

    def get_vols(self, vplex, cluster):
        url = 'https://' + vplex  + '/vplex/clusters/' + cluster + '/virtual-volumes/*'
        j = self._get_request(url, self.request_headers)
        info = j['response']['context']
        return info

    def get_storvols(self, vplex, cluster):
        url = 'https://' + vplex  + '/vplex/clusters/' + cluster + '/storage-elements/storage-volumes/*'
        j = self._get_request(url, self.request_headers)
        info = j['response']['context']
        return info

    def get_devices(self, vplex, cluster):
        url = 'https://' + vplex  + '/vplex/clusters/' + cluster + '/devices/*'
        j = self._get_request(url, self.request_headers)
        info = j['response']['context']
        return info

    def generate_headers(self,vplex):
        # Read encoded passwd from config and decode it. Need to switch this to real encryption
        # when a proper server environment is available.
        pw       = self.VPLEX_LIST[vplex]['password']
        decoded  = base64.b64decode(pw.encode('utf-8')).decode('utf-8')
        # Format the request header for REST calls.
        self.request_headers = {
                'Accept': 'application/json;format=1;prettyprint=1',
                'Username': self.VPLEX_LIST[vplex]['username'],
                'Password': decoded
                }

    # Private Class function
    def _get_request(self, url, request_headers):
        log_dir = '/usr/local/StorageOps/logs'
        logging.basicConfig(filename=log_dir + '/vplexapi.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

        r = requests.get(url, headers=request_headers, verify=False)
        if r.status_code != 200:
            logging.debug('Unexpected HTTP status-code ' + str(r.status_code) + ' for URL=' + url)
            print("Bad status code, (" + str(r.status_code) + ") for " + url)
        return r.json()



            
