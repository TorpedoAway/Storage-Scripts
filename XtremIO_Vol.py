#!/var/www/flask-apps/bin/python3

import sys, os, time
import requests
import json
import urllib3
import yaml, base64

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('/usr/local/StorageOps/etc/endpoints.yaml') as info:
    endpoints = yaml.load(info)

def get_credentials(token):
    p = endpoints[token]['password']
    u =  endpoints[token]['username']
    udecoded = base64.b64decode(u.encode('utf-8')).decode('utf-8')
    pdecoded = base64.b64decode(p.encode('utf-8')).decode('utf-8')
    return [udecoded,pdecoded]



request_headers = {'Accept': 'application/json'}


XIO = dict()


def GetVols(array,username,passwd):
    XIO[array] = dict()
    base_url = 'https://' + array + '/api/json/v2/types/'
    volurl = base_url + '/volumes'
    r = requests.get(volurl, headers=request_headers, verify=False, auth=(username, passwd))
    j = r.json()
    for vol in j["volumes"]:
        url = vol['href']
        XIO[array]['sys_name'] = vol["sys-name"]
        r = requests.get(url, headers=request_headers, verify=False, auth=(username, passwd))
        detail = r.json()
        volname = detail['content']['name']
        XIO[array][volname] = dict()
        XIO[array][volname]['naa'] = detail['content']['naa-name']
        XIO[array][volname]['size'] = detail['content']['vol-size']
        XIO[array][volname]['mappings'] = list()
        mappings = detail['content']['lun-mapping-list']
        for mapping in mappings:
            XIO[array][volname]['mappings'].append(mapping[0][1])




def main():
    arrays = [
                  arraylist_here
             ]
    cred = get_credentials('xio')
    for array in arrays:
        print("Scanning: " + array)
        GetVols(array,cred[0],cred[1])

    xio_vol_map_json = '/usr/local/StorageOps/data/XIO/xio_vol_map_json'
    with open(xio_vol_map_json, "w") as write_file:
        json.dump(XIO, write_file)


# Boiler plate call to main()
if __name__ == '__main__':
  main()

sys.exit()

