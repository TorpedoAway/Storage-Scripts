#!/var/www/flask-apps/bin/python3


import  sys, os, time, re
import  json
sys.path.append('/usr/local/StorageOps/scripts/python_modules')


def Report():
    path = '/usr/local/StorageOps/data/monthly_allocation_report'
    oldfile = path + '/lun_map.json.old'
    newfile = path + '/lun_map.json'
    lunsizefile = '/usr/local/StorageOps/data/sg/lun2size_map.json'
    with open(newfile) as f1:
        newdata = json.load(f1)
    with open(oldfile) as f2:
        olddata = json.load(f2)
    with open(lunsizefile) as f3:
        sizedata = json.load(f3)

    alloc_by_array = dict()
    alloc_by_host  = dict()
    allocations = dict()
    reclaims_by_array = dict()
    arrays = newdata.keys()
    for array in  arrays:
        allocations[array] = dict()
        alloc_by_array[array] = 0
        for lun in newdata[array].keys():
            if lun not in olddata[array]:
                allocations[array][lun] = dict()
                size = '0'
                if lun in sizedata[array]:
                    size = sizedata[array][lun]
                allocations[array][lun]['host'] = newdata[array][lun]
                allocations[array][lun]['size'] = size
                alloc_by_array[array] += int(size)
                host = newdata[array][lun]
                lunkey = array + '_' + lun
                if host not in alloc_by_host:
                    alloc_by_host[host] = dict()
                alloc_by_host[host][lunkey] = size


    for array in  olddata.keys():
        reclaims_by_array[array] = 0
        for lun in olddata[array].keys():
            if lun not in newdata[array]:
                size = '0'
                if lun in sizedata[array]:
                    size = sizedata[array][lun]
                reclaims_by_array[array] += int(size)

    print("Allocations per array")
    for array in alloc_by_array.keys():
        print(array + ":" + str(alloc_by_array[array]))

    print("Reclaims per array")
    for array in reclaims_by_array.keys():
        print(array + " " + str(reclaims_by_array[array]))


    print("Allocations per host")
    for host in alloc_by_host.keys():
        total = 0
        for lunkey in alloc_by_host[host].keys():
            total += int(alloc_by_host[host][lunkey])    
        print(host + ":" + str(total))

    print("Allocations Detail")
    for array in allocations.keys():
        for lun in allocations[array].keys():
            print(array + "\t" + lun + "\t" + allocations[array][lun]['size']  + "\t" + allocations[array][lun]['host'])
   
def main():
    Report()
    

# Boiler plate call to main()
if __name__ == '__main__':
  main()
  
sys.exit()
