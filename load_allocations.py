#!/var/www/flask-apps/bin/python3


import sys, os, time, datetime, csv, base64
import shutil
import requests
import json
import logging
import yaml
from pymongo import MongoClient
#

base_dir = '/usr/local/StorageOps/data/allocations/'
archive  = '/usr/local/StorageOps/data/allocations/archive/'
log_dir  = '/usr/local/StorageOps/logs'

logging.basicConfig(filename=log_dir + '/load_allocations.log',
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
    allocations = db.allocations
    reclaims = db.reclaims
    allocation = dict()
    reclaim = dict()
    for filename in os.listdir(base_dir):
        if not filename.endswith('.json'): continue
        nametmp = filename.replace('.json','')
        fields = nametmp.split('_')
        timestring = fields[len(fields) - 1]
        fullname = os.path.join(base_dir, filename)
        #print(filename)
        with open(fullname, "r") as read_file:
            allocation = json.load(read_file)
            allocation['timestr'] = timestring
            print(allocation)
            post_id = allocations.insert_one(allocation).inserted_id
            logging.debug('Filename: ' + fullname)
            logging.debug('Object ID: ' + str(post_id))
            if post_id:
                shutil.move(fullname,archive)

        
    reclaims_base_dir = '/usr/local/StorageOps/data/reclaims/'
    reclaims_archive  = '/usr/local/StorageOps/data/reclaims/archive/'
    for filename in os.listdir(reclaims_base_dir):
        if not filename.endswith('.json'): continue
        nametmp = filename.replace('.json','')
        fields = nametmp.split('_')
        timestring = fields[len(fields) - 1]
        fullname = os.path.join(reclaims_base_dir, filename)
        with open(fullname, "r") as read_file:
            reclaim = json.load(read_file)
            reclaim['timestr'] = timestring
            print(reclaim)
            post_id = reclaims.insert_one(reclaim).inserted_id
            logging.debug('Filename: ' + fullname)
            logging.debug('Object ID: ' + str(post_id))
            if post_id:
                shutil.move(fullname,reclaims_archive)




# Boiler plate call to main()
if __name__ == '__main__':
  main()
                    
               
sys.exit()


