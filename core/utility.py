import re, logging, os

def remove_password(configuration):
    ret=re.sub(r'snmp-server community \b\w*','snmp-server community <removed>',configuration)
    ret=re.sub(r'snmp-server host ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) version (\w{1,2}) .*','snmp-server host \g<1> version \g<2> <removed>',ret)
    ret=re.sub(r'enable (secret|password) (\d)?.*','enable \g<1> \g<2> <removed>',ret)
    ret=re.sub(r'(\skey\s)\b.*','\g<1><removed>',ret)
    ret=re.sub(r'(\spassword\s[57]\s)\b.*','\g<1><removed>',ret)
    ret=re.sub(r'(\slog trap\s)[^\s.]*','\g<1><removed>',ret)
    return ret

#function write log to file
def write_fail_log_to_file(msg,hostname):
    try:
        outfolder="./fail/"
        outfile=outfolder+"/"+str(datetime.datetime.now().strftime("%Y%m%d-%H.%M.%S"))
        if not os.path.exists(outfolder):
                os.makedirs(outfolder)
        #with open(outfile,"wt") as f:
        #    f.write(str(msg))
        logging.basicConfig(filename=outfile,level=logging.INFO)
        logging.info(str(msg)+" - "+str(hostname))
        #success
        #return "Failed to connect to {}. Log saved in {}".format(hostname,outfolder+"/"+outfile)
    except:
        print(f"Write log to file error {sys.exc_info()[1]}")
        #failure
        #return 0

#function write log to file
def write_log_to_file(config,filename,group,date):
    try:
        outfolder="./"+group+"/"+str(date)
        outfile=outfolder+"/searchresult.log"
        logging.basicConfig(filename=outfile,level=logging.INFO)
        if not os.path.exists(outfolder):
                os.makedirs(outfolder)
        logging.info(config)
        #success
        return "Finish checking site {}. Log saved in {}".format(filename,outfile)
    except:
        return "Write log to file error {0}".format(sys.exc_info()[1])
        #failure
        #return 0


def write_search_output_to_file(output,outfolder):
    try:
        #outfolder="./"+outfolder+"/"+str(datetime.datetime.now().date())
        outfile=str(outfolder)+"/"+str(searchstring)+"output.txt"
        #if not os.path.exists(outfolder):
        #       os.makedirs(outfolder)
        if not os.path.exists(outfile):
            open(outfile,"w").close()
        fp=open(outfile,"a")
        fp.write(output+"\n")
        fp.close()
        #success
        return "Output of site {} - {} saved in {}".format(hostname,host,outfile)
    except:
        return "Write output to file error {} for site {} - {}".format(sys.exc_info()[1],hostname,host)
        #failure
        #return 0