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

base_dir = '/usr/local/StorageOps/data/vplex/Unexported'

logging.basicConfig(filename= '/usr/local/StorageOps/logs/vplexapi.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p')

logging.debug('Starting up....')


def main():
    vp = VPLEX_Tools()
    x = Tools()
                
    # In this section we scan all the vplex arrays listed in the config file and produce an output data file
    # representing current state. While scanning we keep a list of newly added luns which were not in the previous run.
    naafile = base_dir + "/unexported_volumes.txt"
    x.archive_file(naafile)
    f1 = open(naafile,'w')
    uniqnaa = dict()
    for vplex in vp.VPLEX_LIST.keys():
        datafile = base_dir + "/" + vplex + "_unexported_data.txt"
        x.archive_file(datafile)
        f = open(datafile,'w')
        vp.generate_headers(vplex)
        # Iterate over the list of vplex systems and collect unexported vol data.        
        if 'cluster' in vp.VPLEX_LIST[vplex]:
            for cluster in [vp.VPLEX_LIST[vplex]['cluster']]:
                print(vplex, vp.VPLEX_LIST[vplex]['ip'], cluster )
                vols = vp.get_vols(vp.VPLEX_LIST[vplex]['ip'], cluster)
                if vols:
                    for vol in vols:
                        if vol["type"] != "virtual-volume": continue
                        volname = str(vol["name"])
                        capacity = str(vol["capacity"])    
                        tmpcap = capacity.split()
                        capacity = tmpcap[0]
                        export_status = str(vol["service-status"])    
                        naa = str(vol["vpd-id"])    
                        if ( export_status == 'unexported' ):
                            f.write(cluster + "," + volname + ","  + capacity + "," + export_status + "," + naa + "\n")
                            f1.write(vplex + "," + cluster + "," + volname + ","  + capacity + "," + export_status + "," + naa + "\n")
                    

        
# Boiler plate call to main()
if __name__ == '__main__':
  main()
                    
               
sys.exit()





    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
