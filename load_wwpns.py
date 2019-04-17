#!/var/www/flask-apps/bin/python3


import sys, os, time, datetime, csv, base64
import shutil
import requests
import json
import logging
import yaml
from pymongo import MongoClient
#

base_dir = '/usr/local/StorageOps/data/brcd'
log_dir  = '/usr/local/StorageOps/logs'

logging.basicConfig(filename=log_dir + '/load_wwpns.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p')

logging.debug('Starting up....')


def main():
    client = MongoClient()
    #client = MongoClient('localhost', 27017)            
    #client = MongoClient('mongodb://storageguys:Hastings1066@localhost:27017')            
    username = "r2d2"
    password = "3cpo"
    client = MongoClient('mongodb://%s:%s@127.0.0.1:27017/StorageOps?authSource=admin' % (username, password))
    db = client.StorageOps
    wwpns = db.wwpns
    wwpn = dict()
    mapfile = base_dir + "/switch_map.json"
    with open(mapfile) as f:
        data = json.load(f)
    data = get_mds_wwpns(data)
    for wwpn in data.keys():
        aliases = data[wwpn]['aliases']
        devtype = data[wwpn]['devtype']
        label = data[wwpn]['label']
        phywwpn = data[wwpn]['phywwpn']
        port = data[wwpn]['port']
        portindex = data[wwpn]['portindex']
        slot = data[wwpn]['slot']
        switchname = data[wwpn]['switchname']
        lastseen = time.time()
        test = wwpns.find({'wwpn' : wwpn})
        if test.count() == 0:
            newvalues = { 
                             "aliases"     : aliases,
                              "devtype"     : devtype,
                              "label"       : label,
                              "phywwpn"     : phywwpn,
                              "port"        : port,
                              "portindex"   : portindex,
                              "slot"        : slot,
                              "switchname"  : switchname,
                              'wwpn'        : wwpn,
                              "Last_Login"  : lastseen
                        }
            logging.debug("Inserting new WWPN\n",newvalues)
            wwpns.insert_one(newvalues)

        else:
            for result in test:
                newvalues = { "$set":     
                             {"aliases"     : aliases,
                              "devtype"     : devtype,
                              "label"       : label,
                              "phywwpn"     : phywwpn,
                              "port"        : port,
                              "portindex"   : portindex,
                              "slot"        : slot,
                              "switchname"  : switchname,
                              'wwpn'        : wwpn,
                              "Last_Login"  : lastseen}
                    }

                updatequery = { 'wwpn': wwpn }
                wwpns.update_one(updatequery, newvalues)
        #sys.exit()


def get_mds_wwpns(wwpn_login_map):

    switches = dict()
    switches['192.168.0.6'] = 'mds-1'

    #wwpn_login_map = dict()
    wwpn2alias = dict()
    path = '/usr/local/StorageOps/data/mds'
    for filename in os.listdir(path):
        fields = filename.split('_')
        switch_ip = fields[1]
        if 'device-alias' in  filename:
            fullname = os.path.join(path, filename)
            f = open(fullname, 'r')
            for line in f.readlines():
                if line.startswith('device-alias'):
                    fields = line.strip().split()
                    wwpn = fields[4].lower()
                    name = fields[2]
                    wwpn2alias[wwpn] = name

    for filename in os.listdir(path):
        fields = filename.split('_')
        switch_ip = fields[1]
        if 'flogi' in  filename:
            fullname = os.path.join(path, filename)
            f = open(fullname, 'r')
            for line in f.readlines():
                if line.startswith('fc') or line.startswith('port-'):
                    fields = line.strip().split()
                    wwpn = fields[3].lower()
                    connection = fields[0]
                    wwpn_login_map[wwpn] = dict()
                    wwpn_login_map[wwpn]['switchname'] = switches[switch_ip]
                    wwpn_login_map[wwpn]['port'] = connection
                    wwpn_login_map[wwpn]['slot'] = 'N/A'
                    wwpn_login_map[wwpn]['label'] = 'N/A'
                    wwpn_login_map[wwpn]['portindex'] = 'N/A'
                    wwpn_login_map[wwpn]['phywwpn'] = 'N/A'
                    wwpn_login_map[wwpn]['devtype'] = 'N/A'
                    if wwpn in wwpn2alias:
                         wwpn_login_map[wwpn]['aliases'] = wwpn2alias[wwpn]
                    else:
                        wwpn_login_map[wwpn]['aliases'] = 'unknown'

    return wwpn_login_map
# Boiler plate call to main()
if __name__ == '__main__':
  main()
                    
               
sys.exit()


