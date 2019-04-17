#!/var/www/flask-apps/bin/python3

import sys, os, time, base64
import requests
import json
import yaml
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from pymongo import MongoClient
import PyU4V

end_date = int(round(time.time() * 1000))
start_date = end_date - 3600000
client = MongoClient()
#client = MongoClient('localhost', 27017)
#client = MongoClient('mongodb://storageguys:Hastings1066@localhost:27017')
username = "r2d2"
password = "3cpo"
client = MongoClient('mongodb://%s:%s@127.0.0.1:27017/StorageOps?authSource=admin' % (username, password))
db = client.StorageOps
db.vmax3_hosts.drop()
vmax3hosts = db.vmax3_hosts
with open('/usr/local/StorageOps/etc/endpoints.yaml') as info:
    endpoints = yaml.load(info)



def GetHostList(unisphere,port,symid,username,password):
    conn = PyU4V.U4VConn(u4v_version='90',username=username,password=password,server_ip=unisphere,
                         port=port,verify=False,array_id=symid)
    # Commented out get_array_list becasue vmax2 arrays are not supported by the module
    #array_list = conn.common.get_array_list()
    array_list = conn.common.get_v3_or_newer_array_list()
    for array in array_list:
        conn.set_array_id(array)    
        print("Scanning array: " + array)
        host_list = conn.provisioning.get_host_list()
        for host in (host_list):
            host_detail = conn.provisioning.get_host(host)
            host_detail['SID'] = array
            post_id = vmax3hosts.insert_one(host_detail).inserted_id
            #time.sleep(1)
    #hosts_json = '/usr/local/StorageOps/data/restapi/' + array + '_hosts.json'
    #with open(hosts_json, "w") as write_file:
    #    json.dump(Hosts, write_file)


def get_credentials(token):
    p = endpoints[token]['password']
    u =  endpoints[token]['username']
    udecoded = base64.b64decode(u.encode('utf-8')).decode('utf-8')
    pdecoded = base64.b64decode(p.encode('utf-8')).decode('utf-8')
    return [udecoded,pdecoded]


def main():
    unispheres = dict()
    symid = dict()
    unispheres['192.1.111.209'] = '8443'
    unispheres['192.1.111.226'] = '8443'
    unispheres['192.1.111.212'] = '8443'
    unispheres['192.1.111.149'] = '8443'
    # Have to provide a valid symid when connecting to unisphere
    symid['192.1.111.209'] = '000197000123'
    symid['192.1.111.226'] = '000197000124'
    symid['192.1.111.212'] = '000197000125'
    symid['192.1.111.149'] = '000197000126'
    for unisphere,port in unispheres.items():
        cred = get_credentials('unisphere')
        print("Scanning: " + unisphere)
        GetHostList(unisphere,port,symid[unisphere],cred[0],cred[1])



# Boiler plate call to main()
if __name__ == '__main__':
  main()

sys.exit()

