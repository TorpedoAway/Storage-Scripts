  #!/usr/bin/python
  
import re,os,time,datetime,subprocess,sys
import os.path
from shutil import copyfile
import xml.etree.ElementTree as ET
  
class SQLTools:
  
    def MakeTables(self,cur):
        # Make some fresh tables using executescript()
        cur.executescript('''
        DROP TABLE IF EXISTS srdfsummary;
        DROP TABLE IF EXISTS srdfpairs;
        CREATE TABLE srdfsummary (
        id  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
        symdg TEXT, 
        R2_Delta_Time TEXT,
        rdfgrpnum INT,
        status TEXT,
        symid TEXT,
        remotesymid TEXT,
        symcli_host TEXT,
        r1_invalid INT,
        r2_invalid INT
      );
        CREATE TABLE srdfpairs (
        id  INTEGER NOT NULL PRIMARY KEY
            AUTOINCREMENT UNIQUE,
        rdfgrpnum INT,
        R1 TEXT,
        R2 TEXT,
        pair_state TEXT,
        link_state TEXT
      );

      ''')
