#!/var/www/flask-apps/bin/python3

import sys, os, time
import requests
import json
import urllib3
import yaml, base64
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



request_headers = {'Accept': 'application/json'}

with open('/usr/local/StorageOps/etc/endpoints.yaml') as info:
    endpoints = yaml.load(info)

def get_credentials(token):
    p = endpoints[token]['password']
    u =  endpoints[token]['username']
    udecoded = base64.b64decode(u.encode('utf-8')).decode('utf-8')
    pdecoded = base64.b64decode(p.encode('utf-8')).decode('utf-8')
    return [udecoded,pdecoded]



def GetCluster(array,username,passwd):
    base_url = 'https://' + array + '/api/json/v2/types/'
    volurl = base_url + 'clusters/1'
    r = requests.get(volurl, headers=request_headers, verify=False, auth=(username, passwd))
    j = r.json()


    xio_json = '/usr/local/StorageOps/data/XIO/' + array + '.json'
    with open(xio_json, "w") as write_file:
        json.dump(j, write_file)




def main():
    arrays = [
                 arraylist_here
             ]
   

    cred = get_credentials('xio')
    for array in arrays:
        #print(cred)
        GetCluster(array,cred[0],cred[1])

# Boiler plate call to main()
if __name__ == '__main__':
  main()

sys.exit()

