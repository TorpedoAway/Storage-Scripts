#!/var/www/flask-apps/bin/python3


import sys, os, time, datetime, csv, base64
import requests
import json
import logging
import yaml
import urllib3
#
#
# Local module config
sys.path.append('/usr/local/StorageOps/scripts/python_modules')
from vplex_reporting import VPLEX_Tools
from Util import Tools
#
#
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_dir = '/usr/local/StorageOps/data/vplex/Unused'

logging.basicConfig(filename= '/usr/local/StorageOps/logs/vplexapi.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p')

logging.debug('Starting up....')


def main():
    # In this section we scan all the vplex arrays listed in the config file and produce an output data file
    # representing current state. While scanning we keep a list of newly added luns which were not in the previous run.
    vp = VPLEX_Tools()
    x = Tools()
    unused_devices = base_dir + "/unused_devices.txt"
    x.archive_file(unused_devices)
    f1 = open(unused_devices,'w')
    uniqnaa = dict()
    for vplex in vp.VPLEX_LIST.keys():
        datafile = base_dir + "/" + vplex + "_unused_devices.txt"
        x.archive_file(datafile)
        f = open(datafile,'w')
        vp.generate_headers(vplex)
        # Iterate over the list of vplex systems and collect unexported vol data.        
        if 'cluster' in vp.VPLEX_LIST[vplex]:
            for cluster in [vp.VPLEX_LIST[vplex]['cluster']]:
                print(vplex, vp.VPLEX_LIST[vplex]['ip'], cluster )
                devs = vp.get_devices(vp.VPLEX_LIST[vplex]['ip'], cluster)
                if devs:
                    for dev in devs:
                        if dev["type"] != "local-device": continue
                        devname = str(dev["name"])
                        capacity = str(dev["capacity"])    
                        tmpcap = capacity.split()
                        capacity = tmpcap[0]
                        ID = str(dev["system-id"])    
                        vol = str(dev["virtual-volume"])    
                        if vol == 'None':
                            f.write(vplex  + "," + cluster + "," + devname + ","  + capacity +  "\n")
                            f1.write(vplex  + "," + cluster + "," + devname + ","  + capacity + "\n")

        
# Boiler plate call to main()
if __name__ == '__main__':
  main()
                    
               
sys.exit()





    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
