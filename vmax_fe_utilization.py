#!/var/www/flask-apps/bin/python3

import sys, os, time
import requests
import json
import urllib3
import yaml, base64
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


import PyU4V


with open('/usr/local/StorageOps/etc/endpoints.yaml') as info:
    endpoints = yaml.load(info)

def get_credentials(token):
    p = endpoints[token]['password']
    u =  endpoints[token]['username']
    udecoded = base64.b64decode(u.encode('utf-8')).decode('utf-8')
    pdecoded = base64.b64decode(p.encode('utf-8')).decode('utf-8')
    return [udecoded,pdecoded]

end_date = int(round(time.time() * 1000))
start_date = end_date - 3600000


def GetFEPerf(unisphere,port,symid,username,password):
    conn = PyU4V.U4VConn(username=username,password=password,server_ip=unisphere,
                         port=port,verify=False,array_id=symid)
    array_list = conn.common.get_array_list()
    FEutilization = dict()
    for array in array_list:
        conn.set_array_id(array)
        if array not in FEutilization:
            FEutilization[array] = dict()
        print("Begin collection for: " +  array)
        #
        # 1492 gives me a key error???
        #
        try:
            port_list = conn.performance.get_fe_port_list()
        except:
            port_list = dict()
        directors = dict()
        for port in port_list:
            for feport,director in port.items():
                if director not in directors:
                    directors[director] = list()    
                directors[director].append(feport)
        for director in sorted(directors.keys()):
            #print("\t" + director)
            if director not in FEutilization[array]:
                FEutilization[array][director] = dict()   
            for port in directors[director]:
                #print("\t\t" + port)
                if port not in FEutilization[array][director]:
                    FEutilization[array][director][port] = list()
                port_metrics = conn.performance.get_fe_port_util_last4hrs(director,port)
                results = port_metrics[0]['resultList']['result']
                for result in results:
                    FEutilization[array][director][port].append(result)

        
    feperf_json = '/usr/local/StorageOps/data/symmperf/FE_Perf.json'
    with open(feperf_json, "w") as write_file:
        json.dump(FEutilization, write_file)





def main():
    unispheres = dict()
    symid = dict()
    unispheres['IP_Addr'] = 'PORT#'
    # Have to provide a valid symid when connecting to unisphere
    symid['IP_Addr'] = 'SID'
    cred = get_credentials('unisphere')
    for unisphere,port in unispheres.items():
        GetFEPerf(unisphere,port,symid[unisphere],cred[0],cred[1])



# Boiler plate call to main()
if __name__ == '__main__':
  main()

sys.exit()

