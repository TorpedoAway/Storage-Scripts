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
#
#
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from vplex_reporting import VPLEX_Tools
from Util import Tools

base_dir = '/usr/local/StorageOps/data/vplex/Unclaimed'

logging.basicConfig(filename= '/usr/local/StorageOps/logs/vplexapi.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p')

logging.debug('Starting up....')



def main():
    vp = VPLEX_Tools()
    x  = Tools()
                
    # In this section we scan all the vplex arrays listed in the config file and produce an output data file
    # representing current state. While scanning we keep a list of newly added luns which were not in the previous run.
    naafile = base_dir + "/unclaimed_devices.txt"
    claimed_devices = base_dir + "/claimed_devices.txt"
    x.archive_file(naafile)
    x.archive_file(claimed_devices)
    f1 = open(naafile,'w')
    f2 = open(claimed_devices,'w')
    uniqnaa = dict()
    for vplex in vp.VPLEX_LIST.keys():
        datafile = base_dir + "/" + vplex + "_unclaimed.txt"
        x.archive_file(datafile)
        f = open(datafile,'w')
        vp.generate_headers(vplex)
        # Iterate over the list of vplex systems and collect unexported vol data.        
        #for cluster in ['cluster-1']:
        if 'cluster' in vp.VPLEX_LIST[vplex]:
            for cluster in [vp.VPLEX_LIST[vplex]['cluster']]:
                print(vplex, vp.VPLEX_LIST[vplex]['ip'], cluster )
                storvols = vp.get_storvols(vp.VPLEX_LIST[vplex]['ip'], cluster)
                if storvols: 
                    for vol in storvols:
                        if vol["type"] != "storage-volume": continue
                        tdev = 'N/A'
                        volname = str(vol["name"])
                        capacity = str(vol["capacity"])    
                        tmpcap = capacity.split()
                        capacity = tmpcap[0]
                        operational = str(vol["operational-status"])    
                        array = str(vol["storage-array-name"])    
                        naa = str(vol["system-id"])    
                        fields = naa.split(':')
                        if len(fields) > 1:
                            naa = fields[1]
                        if 'SYMM' in array:
                            tdev = x.decode_vmax(naa)
                        use = str(vol["use"])    
                        usedby = ""
                        for uses in vol["used-by"]:
                           usedby += str(uses) + " " 
                        if use == 'unclaimed':
                            f.write(vplex + ',' + cluster + ',' + volname + ',' + array + ','  
                                      + capacity + ',' + operational + ',' + use + ',' + usedby + ',' + tdev + "\n")
                            f1.write(vplex + ',' + cluster + ',' + volname + ',' + array + ','  
                                      + capacity + ',' + operational + ',' + use + ',' + usedby + ',' + tdev + "\n")
                        else:
                            f2.write(vplex + ',' + cluster + ',' + volname + ',' + array + ','
                                     + capacity + ',' + operational + ',' + use + ',' + usedby + ',' + tdev + "\n")
 
                    
        
# Boiler plate call to main()
if __name__ == '__main__':
  main()
                    
               
sys.exit()

