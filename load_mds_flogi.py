#!/var/www/flask-apps/bin/python3


import sys, os, time, datetime, csv, base64
import shutil
#

def main():

    switches = dict()
    switches['192.168.0.6'] = 'mds-1'

    wwpn_login_map = dict()
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


# Boiler plate call to main()
if __name__ == '__main__':
  main()
                    
               
sys.exit()


