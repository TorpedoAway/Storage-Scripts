#!/var/www/flask-apps/bin/python3


import yaml, json, math



class CmdGen:

    def __init__(self,os):
        self.data = []
        self.Aliases = dict()
        self.request = dict()
        self.Ports = dict()
        self.ZoneCmds = list()
        self.StorageCmds = list()
        self.OS = os
        self.ZoneList = dict()


    def GetRequest(self):
        with open('/usr/local/StorageOps/scripts/provision.yaml') as info:
            self.request = yaml.load(info)
        for fabric in self.request['WWPNS'].keys():
            for hba in self.request['WWPNS'][fabric].keys():
                wwpn = self.request['WWPNS'][fabric][hba].replace(':','')
                self.request['WWPNS'][fabric][hba] = wwpn
 
    def LoadPorts(self):
        json_ports = '/usr/local/StorageOps/scripts/ports.json'
        with open(json_ports) as f:
            self.PORTS = json.load(f)

    def BuildCmds(self):
        PG = self.request['STORAGE']['PG']
        host = self.request['HOST']['HOSTNAME']
        self.ZoneCmds.append("\n\n\n\n")
        for fabric in sorted(self.PORTS[PG].keys()):
            self.ZoneList[fabric] = list()
            self.ZoneCmds.append("# Commands for fabric: " + fabric)
            if fabric.endswith('01'):
                self.ZoneCmds.append( self.Aliases['FAB1']['h1a_alias_cmd'])
                self.ZoneCmds.append( self.Aliases['FAB1']['h5a_alias_cmd'])
                if self.OS == 'AIX':
                    self.ZoneCmds.append( self.Aliases['FAB1']['h3p_alias_cmd'])
                    self.ZoneCmds.append( self.Aliases['FAB1']['h7p_alias_cmd'])
                self.BuildZones(fabric,host,PG)
                for zone in self.ZoneList[fabric]:
                   self.ZoneCmds.append("cfgadd " + '"' + fabric + '"'+ ', ' + zone)
            else:
                self.ZoneCmds.append( self.Aliases['FAB2']['h2a_alias_cmd'])
                self.ZoneCmds.append( self.Aliases['FAB2']['h6a_alias_cmd'])
                if self.OS == 'AIX':
                    self.ZoneCmds.append( self.Aliases['FAB2']['h4p_alias_cmd'])
                    self.ZoneCmds.append( self.Aliases['FAB2']['h8p_alias_cmd'])
                self.BuildZones(fabric,host,PG)
                for zone in self.ZoneList[fabric]:
                   self.ZoneCmds.append("cfgadd " + '"' + fabric + '"'+ ', ' + zone)
            self.ZoneCmds.append("cfgenable " + '"' + fabric + '"')
            self.ZoneCmds.append("cfgsave\n\n\n")


    def CreateStorage(self):
        PG = self.request['STORAGE']['PG']
        array = self.request['STORAGE']['ARRAY']
        host = self.request['HOST']['HOSTNAME']
        sg = self.request['HOST']['SG']
        mv = self.request['HOST']['MV']
        ig = self.request['HOST']['IG']
        initiators = dict()
        initiators['h1'] = self.request['WWPNS']['FAB1']['HBA1_ACTIVE']
        initiators['h5'] = self.request['WWPNS']['FAB1']['HBA5_ACTIVE']
        initiators['h2'] = self.request['WWPNS']['FAB2']['HBA2_ACTIVE']
        initiators['h6'] = self.request['WWPNS']['FAB2']['HBA6_ACTIVE']
        if self.OS == 'AIX':
            initiators['h4'] = self.request['WWPNS']['FAB2']['HBA4_PASSIVE']
            initiators['h7'] = self.request['WWPNS']['FAB1']['HBA7_PASSIVE']
            initiators['h8'] = self.request['WWPNS']['FAB2']['HBA8_PASSIVE']
            initiators['h3'] = self.request['WWPNS']['FAB1']['HBA3_PASSIVE']
        if self.request['HOST']['Create'] == 'True':
            self.StorageCmds.append("# SYMCLI Commands")
            self.StorageCmds.append("symaccess -sid " + array + " create -name " + sg + " -type storage")
            self.StorageCmds.append("symsg -sid " + array + " -sg " + sg + " set -com -sl Diamond -srp srp_1")
            self.StorageCmds.append("symaccess -sid " + array + " create -name " + ig + " -type initiator")
        
            for initiator in sorted(initiators.keys()):
                self.StorageCmds.append("symaccess -sid " + array + " -name " + ig + " -type initiator add -wwn " + initiators[initiator])

            for initiator in sorted(initiators.keys()):
                alias =  host + '/' + initiator
                self.StorageCmds.append("symaccess -sid " + array + " rename -wwn " + initiators[initiator] + " -alias " + alias)

        if self.request['STORAGE']['Create'] == 'True':
            for lun in sorted(self.request['STORAGE']['LUNS'].keys()):
                self.StorageCmds.append("# " + lun)
                for c in self.request['STORAGE']['LUNS'][lun].keys():
                    count = c 
                    gb = self.request['STORAGE']['LUNS'][lun][c] 
                    cyl =  (1092.4 * float(gb)) / 2 
                    cyl = math.ceil(cyl) 
                    cmd = "symconfigure -sid " + array + " -cmd " + '"'
                    cmd += "create dev count=" + str(count) + ", size=" + str(cyl) 
                    cmd += " cyl, emulation=fba config=TDEV sg=" + sg + ';"' + " commit -nop"
            
                    self.StorageCmds.append(cmd)
        pg = PG[2:]
        mvcommand = "symaccess -sid " + array + " create view -name " + mv + " -sg " + sg + " -ig " + ig + " -pg " + pg;
        self.StorageCmds.append(mvcommand) 
    


    def BuildZones(self,fabric,host,PG):
        fields = PG.split('_')
        ports = list()
        
        for port in self.PORTS[PG][fabric]:
            for alias in port.keys():
                ports.append(alias)
        if fabric.endswith('01'):
            hostaliases_1_3 =   self.Aliases['FAB1']['h1a_alias']
            hostaliases_5_7 =   self.Aliases['FAB1']['h5a_alias']
            if self.OS == 'AIX':
                hostaliases_1_3 +=    '; ' + self.Aliases['FAB1']['h3p_alias']
                hostaliases_5_7 +=    '; ' + self.Aliases['FAB1']['h7p_alias']
            self.ZoneCmds.append("zonecreate " + '"z_' + host + '_h1_' + fields[0] + '", ' +  '"' + hostaliases_1_3 + '; ' + ports[0] + '"')
            self.ZoneList[fabric].append('"z_' + host + '_h1_' + fields[0] + '"')
            #self.ZoneCmds.append("cfgadd " + '"' + fabric + '"'+ ', ' + '"z_' + host + '_h1_' + fields[0] + '")
            if len(ports) > 1:
               self.ZoneCmds.append("zonecreate " + '"z_' + host + '_h5_' + fields[0] + '", ' +  '"' + hostaliases_5_7 + '; ' + ports[1] + '"')
               self.ZoneList[fabric].append('"z_' + host + '_h5_' + fields[0] + '"')
        else:
            hostaliases_2_4 =   self.Aliases['FAB2']['h2a_alias']
            hostaliases_6_8 =   self.Aliases['FAB2']['h6a_alias']
            if self.OS == 'AIX':
                hostaliases_2_4 +=   '; ' + self.Aliases['FAB2']['h4p_alias']
                hostaliases_6_8 +=   '; ' + self.Aliases['FAB2']['h8p_alias']
            self.ZoneCmds.append("zonecreate " + '"z_' + host + '_h2_' + fields[0] + '", ' +  '"' + hostaliases_2_4 + '; ' + ports[0] + '"')
            self.ZoneList[fabric].append('"z_' + host + '_h2_' + fields[0] + '"')
            if len(ports) > 1:
               self.ZoneCmds.append("zonecreate " + '"z_' + host + '_h6_' + fields[0] + '", ' +  '"' + hostaliases_6_8 + '; ' + ports[1] + '"')
               self.ZoneList[fabric].append('"z_' + host + '_h6_' + fields[0] + '"')



    def FormatAliases(self):
        self.Aliases = dict()
        self.Aliases['FAB1'] = dict()
        self.Aliases['FAB2'] = dict()
        host = self.request['HOST']['HOSTNAME']
        self.Aliases['FAB1']['h1a_wwpn'] = self.request['WWPNS']['FAB1']['HBA1_ACTIVE']
        self.Aliases['FAB1']['h5a_wwpn'] = self.request['WWPNS']['FAB1']['HBA5_ACTIVE']
        self.Aliases['FAB2']['h2a_wwpn'] = self.request['WWPNS']['FAB2']['HBA2_ACTIVE']
        self.Aliases['FAB2']['h6a_wwpn'] = self.request['WWPNS']['FAB2']['HBA6_ACTIVE']

        wwpn = self.FormatWWPN(self.Aliases['FAB1']['h1a_wwpn'])
        self.Aliases['FAB1']['h1a_alias'] = host + '_h1'
        self.Aliases['FAB1']['h1a_alias_cmd'] = 'alicreate ' + '"' + self.Aliases['FAB1']['h1a_alias'] + '"' + ',' + ' "' + wwpn + '"'

        wwpn = self.FormatWWPN(self.Aliases['FAB1']['h5a_wwpn'])
        self.Aliases['FAB1']['h5a_alias'] = host + '_h5'
        self.Aliases['FAB1']['h5a_alias_cmd'] = 'alicreate ' + '"' + self.Aliases['FAB1']['h5a_alias'] + '"' + ',' + ' "' + wwpn + '"'

        wwpn = self.FormatWWPN(self.Aliases['FAB2']['h2a_wwpn'])
        self.Aliases['FAB2']['h2a_alias'] = host + '_h2'
        self.Aliases['FAB2']['h2a_alias_cmd'] = 'alicreate ' + '"' + self.Aliases['FAB2']['h2a_alias'] + '"' + ',' + ' "' + wwpn + '"'

        wwpn = self.FormatWWPN(self.Aliases['FAB2']['h6a_wwpn'])
        self.Aliases['FAB2']['h6a_alias'] = host + '_h6'
        self.Aliases['FAB2']['h6a_alias_cmd'] = 'alicreate ' + '"' + self.Aliases['FAB2']['h6a_alias'] + '"' + ',' + ' "' + wwpn + '"'

        if self.OS == 'AIX':
            self.Aliases['FAB1']['h3p_wwpn'] = self.request['WWPNS']['FAB1']['HBA3_PASSIVE']
            self.Aliases['FAB1']['h7p_wwpn'] = self.request['WWPNS']['FAB1']['HBA7_PASSIVE']
            self.Aliases['FAB2']['h4p_wwpn'] = self.request['WWPNS']['FAB2']['HBA4_PASSIVE']
            self.Aliases['FAB2']['h8p_wwpn'] = self.request['WWPNS']['FAB2']['HBA8_PASSIVE']


            wwpn = self.FormatWWPN(self.Aliases['FAB2']['h8p_wwpn'])
            self.Aliases['FAB2']['h8p_alias'] = host + '_h8'
            self.Aliases['FAB2']['h8p_alias_cmd'] = 'alicreate ' + '"' + self.Aliases['FAB2']['h8p_alias'] + '"' + ',' + ' "' + wwpn + '"'

            wwpn = self.FormatWWPN(self.Aliases['FAB1']['h3p_wwpn'])
            self.Aliases['FAB1']['h3p_alias'] = host + '_h3'
            self.Aliases['FAB1']['h3p_alias_cmd'] = 'alicreate ' + '"' + self.Aliases['FAB1']['h3p_alias'] + '"' + ',' + ' "' + wwpn + '"'

            wwpn = self.FormatWWPN(self.Aliases['FAB1']['h7p_wwpn'])
            self.Aliases['FAB1']['h7p_alias'] = host + '_h7'
            self.Aliases['FAB1']['h7p_alias_cmd'] = 'alicreate ' + '"' + self.Aliases['FAB1']['h7p_alias'] + '"' + ',' + ' "' + wwpn + '"'

            wwpn = self.FormatWWPN(self.Aliases['FAB2']['h4p_wwpn'])
            self.Aliases['FAB2']['h4p_alias'] = host + '_h4'
            self.Aliases['FAB2']['h4p_alias_cmd'] = 'alicreate ' + '"' + self.Aliases['FAB2']['h4p_alias'] + '"' + ',' + ' "' + wwpn + '"'


    def FormatWWPN(self,wwpn):
        wwpn = wwpn.lower()
        wwpn = wwpn.strip()
        wwpn = wwpn.replace(':','')
        pos = 0
        wwpn2 = ''
        while pos < 14:
            wwpn2 += str(wwpn[pos:pos + 2]) + ':'
            pos += 2
        wwpn2 += str(wwpn[pos:pos + 2])
        return wwpn2


    def MakePORTSMap(self):
        PORTS = dict()
        with open('/usr/local/StorageOps/scripts/ports.txt') as f:
            for line in f:
                fields = line.strip().split()
                PG = fields[0]
                ALIAS = fields[1]
                WWPN = fields[2]
                FAB = fields[3]
                if PG not in PORTS:
                    PORTS[PG] = dict()
                if FAB not in PORTS[PG]:
                    PORTS[PG][FAB] = list()
                x = dict()
                x[ALIAS] = WWPN
                PORTS[PG][FAB].append(x)


        json_out = '/usr/local/StorageOps/scripts/ports.json'
        with open(json_out, "w") as write_file:
            json.dump(PORTS, write_file)


