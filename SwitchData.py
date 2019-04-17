#!/var/www/flask-apps/bin/python3


import  sys, os, time, re
import  json
sys.path.append('/usr/local/StorageOps/scripts/python_modules')
from Util import Files
f = Files()

flogi = dict()

def CreateZoneMap():
    GlobalZoneMap = dict()
    GlobalZoneNameMap = dict()
    zonefiles = [
                 'fbrs01_c03_j00a_zoneshow.txt', 
                 'fbrs02_c03_j00w_zoneshow.txt', 
                 'fbsc01_c03_j00f_zoneshow.txt', 
                 'fbsc02_c03_j01s_zoneshow.txt'
                ]
    path = '/usr/local/StorageOps/data/brcd'
    for zonefile in zonefiles:
        file_name = path + '/' + zonefile
        if os.path.exists(file_name):
            with open(file_name, "r") as read_file:
                for line in read_file:
                    if 'Effective configuration' in line:
                        (zonemap,zonenamemap) = GetZones(read_file)
                        GlobalZoneMap.update(zonemap)
                        GlobalZoneNameMap.update(zonenamemap)

    zone_map_json = '/usr/local/StorageOps/data/brcd/zone_map.json'
    zone_name_map_json = '/usr/local/StorageOps/data/brcd/zone_name_map.json'
    with open(zone_map_json, "w") as write_file:
        json.dump(GlobalZoneMap, write_file)
    with open(zone_name_map_json, "w") as write_file:
        json.dump(GlobalZoneNameMap, write_file)
    zonenames = '/usr/local/StorageOps/data/brcd/zonenames.txt'
    zones = GlobalZoneNameMap.keys()
    zonesout = list()
    for zone in sorted(zones):
        zonesout.append(zone + '|' + GlobalZoneNameMap[zone])
    f.write_file(zonenames,zonesout)


               
    



def GetZones(read_file):
    zonemap = dict()
    zonenamemap = dict()
    p = re.compile('..:..:..:..:..:..:..:..')
    for line in read_file:
        line = line.strip()
        if 'cfg:' in line:
            fields = line.split()
            cfg = fields[1]
        if 'zone:' in line:
            fields = line.split()
            zone = fields[1]
        if  p.match(line):
            cfg_zone = cfg + ':' + zone
            wwpn = line
            if line in zonemap:
                zonemap[wwpn] += " " + cfg_zone            
            else:
                zonemap[wwpn] = cfg_zone
            if cfg_zone in zonenamemap:
                zonenamemap[cfg_zone] += " " + wwpn
            else:
                zonenamemap[cfg_zone] =  wwpn
         
    return (zonemap,zonenamemap)



def CreateMap():
    path = '/usr/local/StorageOps/data/brcd'

    for datfile in os.listdir(path):
        if datfile.endswith("_nsshow.txt"):
            switchname = datfile.replace("_nsshow.txt","") 
            switchshowfile = switchname + '_switchshow.txt'
            switchdat = GetSwitchShow(path + '/' + switchshowfile)
            nsshowfile = os.path.join(path, datfile)
            with open(nsshowfile, "r") as read_file:
                for line in read_file:
                    if line.startswith(" N  "):
                        while line.startswith(" N  "):
                            record = get_records(line, read_file)
                            line = record['line']
                            i = record['portindex'].strip()
                            if i in switchdat:
                                label = switchdat[i]['label']
                                slot = switchdat[i]['slot']
                                port = switchdat[i]['port']
                                #print(record['wwpn'],record['phywwpn'],record['devtype'],record['portindex'])
                                #print(slot + '/' + port + "  " + label)
                                flogi[record['wwpn']] = dict()
                                flogi[record['wwpn']]['phywwpn'] = record['phywwpn']
                                flogi[record['wwpn']]['aliases'] = record['aliases']
                                flogi[record['wwpn']]['devtype'] = record['devtype']
                                flogi[record['wwpn']]['portindex'] = record['portindex']
                                flogi[record['wwpn']]['label'] = label
                                flogi[record['wwpn']]['slot'] = slot
                                flogi[record['wwpn']]['port'] = port
                                flogi[record['wwpn']]['switchname'] = switchname
            

    switch_map_json = '/usr/local/StorageOps/data/brcd/switch_map.json'
    with open(switch_map_json, "w") as write_file:
        json.dump(flogi, write_file)


def GetSwitchShow(datfile):
    switchdat = dict()
    p = re.compile('.*..:..:..:..:..:..:..:...*')
    with open(datfile, "r") as read_file:
        for line in read_file:
            if 'switchWwn' in line:
                pass
            elif p.match(line.strip()):
                fields = line.strip().split()
                index = fields[0].strip()
                slot = fields[1]
                port = fields[2]
                if 'slot' in line:
                    label = 'slot' + slot + ' port' + port
                else:
                    label = fields[4]
                switchdat[index] = dict()
                switchdat[index]['slot'] = slot
                switchdat[index]['port'] = port
                switchdat[index]['label'] = label
    return switchdat

def get_records(line, read_file):
    record = dict()
    fields = line.strip().split(';')
    record['wwpn'] = fields[2].lower()
    for line in read_file:
        if "Permanent Port Name" in line:
            fields = line.split('Name:')
            record['phywwpn'] = fields[1].strip() 
        if "Port Index:" in line:
            fields = line.split('Index:')
            record['portindex'] = fields[1].strip()
        if "Device type:" in line:
            fields = line.split('type:')
            record['devtype'] = fields[1].strip()
        if "Aliases:" in line:
            fields = line.split('Aliases:')
            record['aliases'] = fields[1].strip()
        if line.startswith(" N  "):
            record['line'] = line 
            return record            
    record['line'] = 'END'
    return record    


def main():
    CreateMap()
    CreateZoneMap()
    

# Boiler plate call to main()
if __name__ == '__main__':
  main()
  
sys.exit()
