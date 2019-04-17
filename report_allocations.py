#!/var/www/flask-apps/bin/python3


import sys, os, time, datetime, csv, base64
import shutil, pprint
import requests
import json
import logging
import yaml
from pymongo import MongoClient
#

base_dir = '/usr/local/StorageOps/data/allocations/'
archive  = '/usr/local/StorageOps/data/allocations/archive/'
log_dir  = '/usr/local/StorageOps/logs'
pp = pprint.PrettyPrinter(indent=4)


def main():
    results = dict()
    reclaims_results = dict()
    allocation = dict()
    reclaim = dict()
    csvfile = list()
    client = MongoClient()
    #client = MongoClient('localhost', 27017)
    #client = MongoClient('mongodb://storageguys:Hastings1066@localhost:27017')
    username = "r2d2"
    password = "3cpo"
    client = MongoClient('mongodb://%s:%s@127.0.0.1:27017/StorageOps?authSource=admin' % (username, password))
    db = client.StorageOps
    allocations = db.allocations
    reclaims = db.reclaims
    now = time.time()
    timeframe = now - (14*24*60*60)
    for allocation in allocations.find():
        if int(allocation['timestr']) > timeframe:
            results[allocation['_id']] = dict()
            for obj in allocation.keys():
                results[allocation['_id']][obj] = allocation[obj]
    
        
    #pp.pprint(results)
    #sys.exit()
    totalreclaims = 0
    totalallocations = 0
    csvfile.append("\n\nAllocations:\n\n")
    csvfile.append("Change,CPM,Date,SID,Size(GB),LUN,SG")
    for obj in results:
        allocation = results[obj]
        totalallocations += allocation['totalsize']
        csvfile.append(
            allocation['chg'] + ',' +
            allocation['cpm']  + ',' +
            allocation['date']  + ',' +
            str(allocation['sid'])  + ',' +
            str(allocation['totalsize'])  + ',' +
            allocation['lun_ids'].strip()  + ',' +
            allocation['sg']
        )



    for reclaim in reclaims.find():
        if int(reclaim['timestr']) > timeframe:
            reclaims_results[reclaim['_id']] = dict()
            for obj in reclaim.keys():
                #print(obj,reclaim[obj])
                reclaims_results[reclaim['_id']][obj] = reclaim[obj]


    csvfile.append("\n\nReclaims:\n\n")
    csvfile.append("Change,Date,SID,Size(GB),LUN,SG")
    for obj in reclaims_results:
        reclaim = reclaims_results[obj]
        totalreclaims += float(reclaim['size'])
        csvfile.append(
            reclaim['chg'] + ',' +
            reclaim['date'] + ',' +
            str(reclaim['sid']) + ',' +
            str(reclaim['size']) + ',' +
            reclaim['lun_ids'].strip() + ',' +
            reclaim['sg']
        )


    outfile = '/var/www/flask-apps/StorageOps/static/reports/allocations.csv'
    f = open(outfile,"w") 
    f.write("Total Reclaimed: " + str(totalreclaims) + "\n")
    f.write("Total allocated: " + str(totalallocations) + "\n")
    for line in csvfile:
        f.write(line + "\n")
    f.close()


# Boiler plate call to main()
if __name__ == '__main__':
  main()
                    
               
sys.exit()


