#!/usr/bin/python

import re,os,time,datetime,subprocess,sys
import os.path,json
from shutil import copyfile
import xml.etree.ElementTree as ET


class SRDF:

    def __init__(self):
    
        self.SRDF_GRP_Status = dict()
        self.SRDF_GRP_Type = dict()
        self.SRDF_GRP_Suspended = dict()
        self.SRDF_GRP_Pairs = dict()
        self.SRDF_GRP_Links = dict()
        self.SRDF_GRP_GRPNUM = dict()
        self.SRDF_GRP_Delta = dict()
        self.SRDF_GRP_R2Consistent = dict()
        self.SRDF_GRP_R1InvalidMB = dict()
        self.SRDF_GRP_R2InvalidMB = dict()
        self.SRDF_GRP_SYMID = dict()
        self.SRDF_GRP_REMOTESYMID = dict()
        self.SRDF_GRP_SRCHOST = dict()
        self.SRDF_GRP_TGTHOST = dict()
        lun_map_json = '/usr/local/StorageOps/data/sg/lun_map.json'
        with open(lun_map_json, "r") as read_file:
            self.lunmap = json.load(read_file)



    def GetSRDFData(self,hostname):
        path = '/usr/local/StorageOps/data/srdf'
        for filename in os.listdir(path):
            if not filename.startswith(hostname): continue
            fullname = os.path.join(path, filename)
            #print(filename)
            ParseError = 'xml.etree.ElementTree.ParseError'
            try:
                tree = ET.parse(fullname)
            except:
                print("Parsing error occurred while parsing " + filename)
                pass
            root = tree.getroot()
            groupname = ''
            for dg in  root.findall('DG'):
               for dg in  root.findall('DG'):
                   info = dg.find('DG_Info')
                   for node in info:
                       if node.tag == 'name':
                           groupname = node.text
                       if node.tag == 'symid':
                           symid = node.text
                       if node.tag == 'remote_symid':
                           remote_symid = node.text
                       if node.tag == 'ra_group_num':
                           ra_group_num = node.text
                       if node.tag == 'rdfa_time_r2_is_behind_r1':
                           r2deltatime = node.text
                       if node.tag == 'r2_data_is_consistent':
                           self.SRDF_GRP_R2Consistent[groupname] = node.text
                       if node.tag == 'type':
                           self.SRDF_GRP_Type[groupname] = node.text
                   self.SRDF_GRP_SYMID[groupname] = symid
                   self.SRDF_GRP_REMOTESYMID[groupname] = remote_symid
                   self.SRDF_GRP_GRPNUM[groupname] = ra_group_num
                   self.SRDF_GRP_Delta[groupname] = r2deltatime
                   self.SRDF_GRP_Status[groupname] = 'Consistent'
                   pairs = list()
                   for pair in dg.findall('RDF_Pair_Totals'):
                      for node in pair:
                          if node.tag == 'Source':
                               for src in node:
                                   if src.tag == 'r1_invalid_mbs':
                                       self.SRDF_GRP_R1InvalidMB[groupname] = src.text
                                   if src.tag == 'r2_invalid_mbs':
                                       self.SRDF_GRP_R2InvalidMB[groupname] = src.text


                   for pair in dg.findall('RDF_Pair'):
                       for node in pair:
                           if node.tag == 'link_status':
                               link_status = node.text
                           if node.tag == 'pair_state':
                               pair_state = node.text
                               if pair_state != 'Consistent':
                                   self.SRDF_GRP_Status[groupname] = "Not_Consistent"
                               if pair_state == 'Suspended':
                                   self.SRDF_GRP_Suspended[groupname] = "Suspended"
                               if pair_state == 'Split':
                                   self.SRDF_GRP_Status[groupname] = "Split"
                           if node.tag == 'mode':
                               mode = node.text
                      
                           if node.tag == 'Source':
                               for src in node:
                                   if src.tag == 'dev_name':
                                       src_dev = src.text

                           if node.tag == 'Target':
                               for tgt in node:
                                   if tgt.tag == 'dev_name':
                                       tgt_dev = tgt.text
                       srdfhosts = self.GetHosts(groupname,src_dev,tgt_dev)     
                       line = src_dev + "," + tgt_dev + "," + mode + "," + pair_state + "," + link_status
                       line += "," + srdfhosts[0]  + "," + srdfhosts[1]
                       pairs.append(line)
                   self.SRDF_GRP_Pairs[groupname] = pairs


    def GetHosts(self,group,r1,r2):
        srchost = 'N/A'
        tgthost = 'N/A'
        symid = self.SRDF_GRP_SYMID[group][-4:]
        remotesymid = self.SRDF_GRP_REMOTESYMID[group][-4:]
        if self.SRDF_GRP_Type[group] == 'RDF2':
            symid = self.SRDF_GRP_REMOTESYMID[group][-4:]
            remotesymid = self.SRDF_GRP_SYMID[group][-4:]
        if symid in self.lunmap:
            if r1 in self.lunmap[symid]:
                srchost = self.lunmap[symid][r1]    
                srchost = srchost.replace(',',' - ')
        if remotesymid in self.lunmap:
            if r2 in self.lunmap[remotesymid]:
                tgthost = self.lunmap[remotesymid][r2]    
                tgthost = tgthost.replace(',',' - ')
        self.SRDF_GRP_SRCHOST[group] = srchost
        self.SRDF_GRP_TGTHOST[group] = tgthost
        return [srchost,tgthost]
        
            
