#!/var/www/flask-apps/bin/python3


import sys, os, time, datetime, csv, base64
import requests
import json
import logging
import yaml
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
#
sys.path.append('/usr/local/StorageOps/scripts/python_modules')
from vplex_reporting import VPLEX_Tools

base_dir = '/usr/local/StorageOps/data/vplex/Views'
log_dir = '/usr/local/StorageOps/logs'

logging.basicConfig(filename=log_dir + '/vplexapi.log',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s', 
                    datefmt='%m/%d/%Y %I:%M:%S %p')

logging.debug('Starting up....')


def main():
    # In this section we're archiving the old vplexdata file if it exists and we load it into 
    # memory to use as comparison to existing data. 
    vp = VPLEX_Tools()
    today = datetime.datetime.today().strftime('%Y-%m-%d-%H%M-%S')
    archive_exists = False
    additions = list()
    datafile = base_dir + "/vplexdata.txt"
    archive = datafile + '_' + today + '.old'
    previous_changes = base_dir + '/Adds_Removes' + '_' + today + '.old'
    archive_data = dict()
    archive_data_list = list()
    vplexdata_list = list()
    if os.path.isfile(datafile):
        os.rename(datafile, archive)
        archive_exists = True
        with open(archive) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                # We use the dictionary to find additiona and the list to 
                # find reclaims.
                archive_data[row[4]] = row[3]
                s = ",".join(row)
                nospace = "".join(s.split())
                archive_data_list.append( nospace )
                
    # In this section we scan all the vplex arrays listed in the config file and produce an output data file
    # representing current state. While scanning we keep a list of newly added luns which were not in the previous run.
    f = open(datafile,'w')
    for vplex in vp.VPLEX_LIST.keys():
        vplexdatafile = base_dir + "/" + vplex + "vplexview.txt"
        f1 = open(vplexdatafile,'w')

        vp.generate_headers(vplex)
        # Iterate over the list of vplex systems and collect view/vol data.        
        
        if 'cluster' in vp.VPLEX_LIST[vplex]:
            for cluster in [vp.VPLEX_LIST[vplex]['cluster']]:
                print(vplex, vp.VPLEX_LIST[vplex]['ip'], cluster )
                storage_views = vp.get_views(vp.VPLEX_LIST[vplex]['ip'], cluster)
                if storage_views:
                    for storage_view in storage_views:
                        if storage_view["type"] != "storage-view": continue
                        view = storage_view["name"]
                        vols = storage_view["virtual-volumes"]
                        for index, vol in enumerate(vols):
                            vols[index] = vol.replace('(', '').replace(')', '')               
                            fields = vol.split(',')
                            volsize = fields[3].replace(')','')
                        
                            f.write(vplex + ", " + cluster + ", " + view + ", " + fields[1] + ","  + fields[2]  + ","  + volsize + "\n")
                            f1.write(vplex + ", " + cluster + ", " + view + ", " + fields[1] + ","  + fields[2] + ","  + volsize + "\n")
                            s = ",".join([ vplex, cluster, view, fields[1], fields[2], fields[3]])
                            nospace = "".join(s.split())
                            vplexdata_list.append(nospace)
                            if archive_exists:
                                if fields[2] not in archive_data:
                                    additions.append(vplex + ", " + cluster + ", " + view + ", " + fields[1] + ","  + fields[2] + ","  + volsize)
    
    # Create the adds and reclaims file. 
    f.close()
    if os.path.isfile(base_dir + "Adds_Removes.txt"):
        os.rename(base_dir + "/Adds_Removes.txt", previous_changes)
    
    f = open("Adds_Removes.txt",'w')
    f.write("Additions:\n")
    for addition in additions:
        f.write(addition + "\n")
    reclaims = 0
    f.write("\n\nReclaims:\n")
    for line in archive_data_list:
        if line not in vplexdata_list:
            f.write(line + "\n")  
            reclaims += 1            
    f.close()
    if len(additions) + reclaims > 0:
        print("Additions and/or reclaims are listed in Adds_Removes.txt")    

        
# Boiler plate call to main()
if __name__ == '__main__':
  main()
                    
               
sys.exit()


