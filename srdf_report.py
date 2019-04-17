#!/var/www/flask-apps/bin/python3


import base64, sys
sys.path.append('/usr/local/StorageOps/scripts/python_modules')

from vmax_reporting import SRDF


def CreateReport():
    symcli_hosts = [ 'host1', 'host2', 'host3', 'host4']
    summarypage = 'srdf_summary.csv'
    summ_fh = open('/var/www/flask-apps/StorageOps/data/' + summarypage, "w")
    summ_fh.write("SYMCLI_Host,Disk_GROUP,R2_Delta_Time,Group #,Status,Source SymID,Target SymmId,SRC Host, TGT Host\n")
    groups_seen = list()
    for host in symcli_hosts:
        repl = SRDF()
        repl.GetSRDFData(host)
        groups = repl.SRDF_GRP_Pairs.keys()
        for group in groups:
                #if group not in groups_seen:
                groups_seen.append(group)
                grppagename = host + '_' + group + '.html'
                status = repl.SRDF_GRP_Status[group]
                if repl.SRDF_GRP_R2Consistent[group] == 'False':
                    status = 'R2_Not_Consistent'
                delta = float(repl.SRDF_GRP_R1InvalidMB[group]) + float(repl.SRDF_GRP_R2InvalidMB[group])           
                if delta > 150000:
                    status = 'Falling_Behind'
                if group in repl.SRDF_GRP_Suspended:
                    status = 'Suspended'
                if repl.SRDF_GRP_Status[group] == 'Split':
                    status = 'Split'
    
                symid = repl.SRDF_GRP_SYMID[group]
                remotesymid = repl.SRDF_GRP_REMOTESYMID[group]
                # If this is an RDF2 group, swap symid and remotesymid
                if repl.SRDF_GRP_Type[group] == 'RDF2':
                    symid = repl.SRDF_GRP_REMOTESYMID[group]
                    remotesymid = repl.SRDF_GRP_SYMID[group]
                grp_fh = open('/var/www/flask-apps/StorageOps/static/srdf/' + grppagename, "w")
                summ_fh.write(host + "," + group 
                              + "," + repl.SRDF_GRP_Delta[group] 
                              + "," + repl.SRDF_GRP_GRPNUM[group] 
                              + "," + status
                              + "," + symid
                              + "," + remotesymid
                              + "," + repl.SRDF_GRP_SRCHOST[group]
                              + "," + repl.SRDF_GRP_TGTHOST[group]
                              +  "\n")            
                grp_fh.write(grp_header(group))
                linkfile = host + '_' + group + '.xml' 
                link = '<a href=/StorageView/static/srdf/xml/' + linkfile + '>XML Output</a>'
                grp_fh.write("<p>" + link + "<br>")
                grp_fh.write("<table border=1>\n<tr><th>Source SymmID<th>Target SymmID")
                grp_fh.write("<tr><td>" + symid )
                grp_fh.write("<td>" + remotesymid )
                grp_fh.write("</tr></table>")

                # Spacing
                grp_fh.write("<table border=0><tr><td><tr><td></table>")
    
                grp_fh.write("<table border=1>\n<tr><th>Status<th>RDF Grp<th>R2 Delta Time<th>SYMCLI Host")
                grp_fh.write("<th>R1 Invalid MB/s<th>R2 Invalid MB/s Grp")
                grp_fh.write("<tr><td>" + status)
                grp_fh.write("<td>" +  repl.SRDF_GRP_GRPNUM[group])
                grp_fh.write("<td>" +  repl.SRDF_GRP_Delta[group])
                grp_fh.write("<td>" +  host)
                grp_fh.write("<td>" +  repl.SRDF_GRP_R1InvalidMB[group])
                grp_fh.write("<td>" + repl.SRDF_GRP_R2InvalidMB[group])
                grp_fh.write("</tr></table>")

                grp_fh.write("<table border=0><tr><td><tr><td></table>")
                grp_fh.write("<table border=0><tr><td><tr><td></table>")

                grp_fh.write(grp_table(repl,group))
                grp_fh.write("</body>\n</html>")


def grp_table(repl,group):
    table = "<table border=1>\n"
    table += "<tr><th>R1<th>R2<th>Mode<th>Pair State<th>Link State<th>SRC Host<th>TGT Host</tr>"
    for pair in repl.SRDF_GRP_Pairs[group]:
        table += "<tr>"
        fields = pair.split(',')
        for field in fields:
            table += "<td>" + field
        table += "</tr>\n"
    table += "</table>\n"
    return table



def grp_header(group):
    header = "<html>\n<head><title>SRDF Group Page for " + group + "</title>\n"
    header += "<meta http-equiv=\"refresh\" content=\"300\"/></head>\n<body>\n"
    header += "<p><h4>\nSRDF Status Page: " + group + "</h4><br>\n"
    return header

def main():
    CreateReport()
    

# Boiler plate call to main()
if __name__ == '__main__':
  main()
  
sys.exit()
