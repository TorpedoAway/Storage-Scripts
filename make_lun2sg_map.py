#!/var/www/flask-apps/bin/python3


import  sys, os
import  json
sys.path.append('/usr/local/StorageOps/scripts/python_modules')

lun2sg = dict()
sg2mv  = dict()
mastermv = dict()

def CreateMap():
    group1 = '/usr/local/StorageOps/data/sg/group1'
    group2 = '/usr/local/StorageOps/data/sg/group2'
    lun_map_json = '/usr/local/StorageOps/data/sg/lun_map.json'
    for datafile in [group1, group1]:
        ParseData(datafile)
    with open(lun_map_json, "w") as write_file:
        json.dump(lun2sg, write_file)    


def CreateReplMap():
    clones = dict()
    group1 = '/usr/local/StorageOps/data/sg/group1_clone.txt'
    group2 = '/usr/local/StorageOps/data/sg/group2_clone.txt'
    clone_map_json = '/usr/local/StorageOps/data/sg/clone_map.json'
    for datafile in [group1cloneluns, group2cloneluns]:
        clones = ParseReplData(clones,datafile)
    with open(clone_map_json, "w") as write_file:
        json.dump(clones, write_file)


    rdfluns = dict()
    group1rdfluns = '/usr/local/StorageOps/data/sg/group1_rdfluns.txt'
    group2rdfluns = '/usr/local/StorageOps/data/sg/group2_rdfluns.txt'
    rdf_map_json = '/usr/local/StorageOps/data/sg/rdf_map.json'
    for datafile in [group1rdfluns, group2rdfluns]:
        rdfluns = ParseReplData(rdfluns,datafile)
    with open(rdf_map_json, "w") as write_file:
        json.dump(rdfluns, write_file)

def CreateMVMap():
    group1mvs = '/usr/local/StorageOps/data/mv/group1_mv_detail'
    group2mvs = '/usr/local/StorageOps/data/mv/group2_mv_detail'
    sg2mv_map_json = '/usr/local/StorageOps/data/sg/sg2mv_map.json'
    mastermv_map_json = '/usr/local/StorageOps/data/sg/mastermv_map.json'
    for datafile in [group1mvs, group2mvs]:
        ParseMVData(datafile)
    with open(sg2mv_map_json, "w") as write_file:
        json.dump(sg2mv, write_file)
    with open(mastermv_map_json, "w") as write_file:
        json.dump(mastermv, write_file)


def CreateLun2SizeMap():
    lunsizemap = dict()
    path = '/usr/local/StorageOps/data/sg'
    for filename in os.listdir(path):
        if not filename.endswith('_lun_sizes'): continue
        fields = filename.split('_')
        array = fields[0]
        lunsizemap[array] = dict()
        fullname = os.path.join(path, filename)
        with open(fullname, "r") as f:
            for line in f.readlines():
                fields = line.strip().split()
                if len(fields) == 2:
                    lun_id = fields[0]
                    mb = fields[1]
                    lunsizemap[array][lun_id] = mb
    lun2size_map_json = '/usr/local/StorageOps/data/sg/lun2size_map.json'
    with open(lun2size_map_json, "w") as write_file:
        json.dump(lunsizemap, write_file)

    
                        


def ParseData(datafile):
    fh1 = open(datafile, 'r')
    for line in fh1.readlines():
        line = line.strip()
        fields = line.split('|')
        array  = fields[0].strip()
        lun    = fields[1].strip()
        sg     = fields[2].strip()
        if array in lun2sg:
            if lun in lun2sg[array]:
                lun2sg[array][lun] += ", " + sg.lower()
            else:
                lun2sg[array][lun] =  sg.lower()
        else:
            lun2sg[array] = dict()
            lun2sg[array][lun] =  sg.lower()
  
def ParseReplData(devs,datafile):
    fh1 = open(datafile, 'r')
    for line in fh1.readlines():
        line = line.strip()
        fields = line.split()
        array  = fields[0].strip()
        lun    = fields[1].strip()
        if array not in devs:
            devs[array] = dict()
        devs[array][lun.upper()] = 1
    return devs

def ParseMVData(datafile):
    fh1 = open(datafile, 'r')
    for line in fh1.readlines():
        line    = line.strip()
        fields  = line.split(':')
        array   = fields[0].strip()
        objtype = fields[1].strip()
        name    = str(fields[2].strip())
        if array not in sg2mv:
            sg2mv[array] = dict()
        if array not in mastermv:
            mastermv[array] = dict()

        if 'Masking View' in objtype:
            view = name
        elif 'Port Group' in objtype:
            pg = name
        elif 'Initiator Group' in objtype:
            ig = name
        elif 'Storage Group' in objtype:
            sg = name.lower()
            mastermv[array][view] = dict()
            mastermv[array][view]['PG'] = pg
            mastermv[array][view]['IG'] = ig
            mastermv[array][view]['SG'] = name
            if sg not in sg2mv:
                sg2mv[array][sg] = dict()
                sg2mv[array][sg]['MV'] = list()
                sg2mv[array][sg]['PG'] = list()
                sg2mv[array][sg]['IG'] = list()
                sg2mv[array][sg]['MV'].append(view)
                sg2mv[array][sg]['PG'].append(pg)
                sg2mv[array][sg]['IG'].append(ig)
            else:
                sg2mv[array][sg]['MV'].append(view)
                sg2mv[array][sg]['PG'].append(pg)
                sg2mv[array][sg]['IG'].append(ig)

def main():
    CreateMap()
    CreateMVMap()
    CreateLun2SizeMap()
    CreateReplMap()
    

# Boiler plate call to main()
if __name__ == '__main__':
  main()
  
sys.exit()
