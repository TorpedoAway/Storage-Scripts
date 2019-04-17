#!/var/www/flask-apps/bin/python3

import sys, os, time
import json

fe_perf_json = '/usr/local/StorageOps/data/symmperf/FE_Perf.json'
with open(fe_perf_json) as f:
    data = json.load(f)



for symid in data.keys():
    print(symid)
    for director in data[symid]:
        print(director)
        for port in data[symid][director].keys():
            print("Port: " + str(port))
            for result in data[symid][director][port]:
                print(result['timestamp'], result['PercentBusy'])
