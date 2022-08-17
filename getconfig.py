#!
#Name: Get and Find Configuration from Cisco IOS Devices
#Author: Tuan Hoang
#Version: 1.0
#

import concurrent.futures, time, json, sys, datetime, csv, re, argparse, os, logging
from napalm import get_network_driver
from cryptography.fernet import Fernet

############## VARIABLES ##############
username=str(os.environ.get("acc"))
password=str(os.environ.get("cred"))
encryptionkey=str(os.environ.get("enckey"))
#######################################
class bcolors:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def decryptcred(ciphertext):
    fernet = Fernet(bytes(encryptionkey,'utf-8'))
    plaintext = fernet.decrypt(bytes(ciphertext,'utf-8')).decode()
    return plaintext


def removepassword(configuration):
    ret=re.sub(r'snmp-server community \b\w*','snmp-server community <removed>',configuration)
    ret=re.sub(r'snmp-server host ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) version (\w{1,2}) .*','snmp-server host \g<1> version \g<2> <removed>',ret)
    ret=re.sub(r'enable (secret|password) (\d)?.*','enable \g<1> \g<2> <removed>',ret)
    ret=re.sub(r'(\skey\s)\b.*','\g<1><removed>',ret)
    ret=re.sub(r'(\spassword\s[57]\s)\b.*','\g<1><removed>',ret)
    ret=re.sub(r'(\slog trap\s)[^\s.]*','\g<1><removed>',ret)
    return ret
   
def getconfig(hostname,host,user,password,cmd):
    print(f"Connecting to {hostname} - {host}")
    try:
        driver=get_network_driver('ios')
        #This is for ssh connection
        device=driver(host,user,password)
        device.open()
        r=device.cli(commands=[cmd])
        device.close()
        return str(hostname) + " - " + str(host) + " Configuration:\n" + removepassword(r[cmd])    
    except:
        try:
            #print("Trying telnet")
            driver=get_network_driver('ios')
            #This is for telnet connection
            device=driver(host,user,password,optional_args={"transport":"telnet"})
            device.open()
            r=device.cli(commands=[cmd])
            device.close()
            return str(hostname) + " - " + str(host) + " Configuration:\n" + removepassword(r[cmd]) 
        except:
            writefaillogtofile(sys.exc_info()[1],hostname+"-"+host)
            #return "Error: " + str(sys.exc_info()[1]) + " " + str(hostname) + " - " + str(host)
            return f"{bcolors.RED}{sys.exc_info()[1]} for site {hostname} - {host}{bcolors.ENDC}"

#function write config to file
def getconfigtofile(hostname,host,user,password,cmd,outfolder):
    try:
        output=getconfig(hostname,host,user,password,cmd)
        #outfolder="./"+outfolder+"/"+str(datetime.datetime.now().date())
        outfile=str(outfolder)+"/"+hostname+".txt"
        if not os.path.exists(outfolder):
                os.makedirs(outfolder)
        fp=open(outfile,"w")
        fp.write(output)
        fp.close()
        #success
        return f"{bcolors.BLUE}Configuration of site {hostname} - {host} saved in {outfile}{bcolors.ENDC}"
    except:
        return f"{bcolors.RED}Write configuration to file error {sys.exc_info()[1]} for site {hostname} - {host}{bcolors.ENDC}"
        #failure
        #return 0

def searchconfig(hostname,host,user,password,cmd,searchstring):
    try:
        driver=get_network_driver('ios')
        device=driver(host,user,password)
        device.open()
        r=device.cli(commands=[str(cmd)])

        if str(searchstring) in r[str(cmd)]:
            return str(hostname) + " - " + str(host) + ": " + str(searchstring) + " in " + str(cmd)
        else:
            return str(hostname) + " - " + str(host) + ": not existed"
        device.close()
    except:
        #print(f"Error: {str(sys.exc_info()[1])} {str(hostname)}")
        try:
            driver=get_network_driver('ios')
            device=driver(host,user,password,optional_args={"transport":"telnet"})
            device.open()
            r=device.cli(commands=[str(cmd)])

            if str(searchstring) in r[str(cmd)]:
               return str(hostname) + " - " + str(host) + ": " + str(searchstring) + " in " + str(cmd)
            else:
               return str(hostname) + " - " + str(host) + ": not existed" 
            device.close()
        except:
            return "Error: " + str(sys.exc_info()[1]) + " " + str(hostname) + " - " + str(host)

def writesearchoutputtofile(output,outfolder):
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

#function write log to file
def writefaillogtofile(msg,hostname):
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
def getusername(user):
    #print(user,username)
    if str(user) == "":
        return username
    else:
        return decryptcred(user)

def getpassword(passw):
    #print(passw,password)
    if str(passw) == "":
        return password
    else:
        return decryptcred(passw)

#function write log to file
def writelogtofile(config,filename,group,date):
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


def startinteractivesession(hostname,host,user,password):
    try:
        driver=get_network_driver('ios')
        #This is for ssh connection
        device=driver(host,user,password)
        device.open()
        cmd=""
        while cmd != "quit" or cmd != "q":
            cmd=input("Command: ")
            if cmd=="quit" or cmd == "q":
                break
            r=device.cli(commands=[cmd])
            print(r[cmd])
        device.close()
        #return str(hostname) + " - " + str(host) + " Configuration:\n" + removepassword(r[cmd])    
    except:
        try:
            driver=get_network_driver('ios')
            #This is for telnet connection
            device=driver(host,user,password,optional_args={"transport":"telnet"})
            device.open()
            cmd=""
            while cmd != "quit" or cmd != "q":
                cmd=input("Command: ")
                if cmd=="quit" or cmd == "q":
                    break
                r=device.cli(commands=[cmd])
                print(r[cmd])
            device.close()
            #return str(hostname) + " - " + str(host) + " Configuration:\n" + removepassword(r[cmd]) 
        except:
            return "Error: " + str(sys.exc_info()[1]) + " " + str(hostname) + " - " + str(host)

def main():
    parser=argparse.ArgumentParser(description='Get Configuration')
    #parser.add_argument('-c','--command',type=str,metavar='',help='Command to run')
    parser.add_argument('-f','--find',type=str,metavar='',help='Keyword to find')
    parser.add_argument('-l','--list',type=str,metavar='',required=True,help='Device List File')
    parser.add_argument('-s','--site',type=str,metavar='',help='Site to run command')
    parser.add_argument('-w','--writefile',type=str,metavar='',help='Write to File')
    #parser.add_argument('-i','--interactive',action='store_true',help='Interactive Session')
    group=parser.add_mutually_exclusive_group()
    group.add_argument('-c','--command',type=str,metavar='',help='Command to run')
    group.add_argument('-i','--interactive',action='store_true',help='Interactive Session')
    args=parser.parse_args() 
    try:
        #Read devices file
        csvfile=args.list
        srcfile = open(csvfile,"rt")
        reader = csv.DictReader(srcfile)
    except:
        msg = str(datetime.datetime.now())+": "+str(sys.exc_info()[1])
        print(msg)
        sys.exit(1)

    cmd = str(args.command)
    findstring = str(args.find)
    t1=time.perf_counter()
    if args.interactive: # interactive mode -i, can't use with -c
        for i in reader:
            if i["Name"] == str(args.site):
                startinteractivesession(i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]))
    elif args.writefile: #non-interactive mode -c, write to file -w <folder>
        if args.site and args.find: #find keyword from command on 1 site
            # print("find command in one site")
            for i in reader:
                if i["Name"] == str(args.site):
                    result=searchconfig(i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]),cmd,findstring,args.writefile)
                    outfile=str(args.writefile)+"/"+i["Name"]+"output.txt"
                    with open(outfile,'w') as file:
                        print("Output of site {} - {} saved in {}".format(hostname,host,outfile))
                        file.write(r.result())   
        elif not args.site and args.find: #find keyword from command on all sites
            # print("find command in all sites")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results=[executor.submit(searchconfig,i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]),cmd,findstring) for i in reader if i['Name'][0:1] != "#"]
                # for r in results:
                #     print(r.result())
                outfile=str(args.writefile)+"/"+"find output.txt "
                print("Search Result is being saved in {}".format(outfile))
                with open(outfile,'w') as file:
                    for r in results:
                        print(".")
                        file.write(r.result()+"\n")   
        elif args.site and not args.find: #run command on 1 site
            # print( "get config from one site")
            for i in reader:
                if i["Name"] == str(args.site):
                    print(getconfigtofile(i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]),cmd,args.writefile))
        else:# not args.site and not args.find: run command from all sites
            if args.writefile: #write to file
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results=[executor.submit(getconfigtofile,i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]),cmd,args.writefile) for i in reader if i["Name"][0:1] != "#"]
                    for r in results:
                        print(r.result())
    else: #non-interactive mode -c, write to stdout, without -w
        if args.site and args.find: #1 site + find keywords
            # print("find command in one site")
            for i in reader:
                if i["Name"] == str(args.site):
                    print(searchconfig(i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]),cmd,findstring))
        elif not args.site and args.find: # all sites + find keywords
            # print("find command in all sites")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results=[executor.submit(searchconfig,i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]),cmd,findstring) for i in reader if i['Name'][0:1] != "#"]
                for r in results:
                    print(r.result())
        elif args.site and not args.find: # run command on 1 site
            # print( "get config from one site")
            for i in reader:
                if i["Name"] == str(args.site):
                    print(getconfig(i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]),cmd))
        else:# not args.site and not args.find: run command on all sites
            # print("get config from all sites")         
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results=[executor.submit(getconfig,i["Name"],i["Host"],getusername(i["Username"]),getpassword(i["Password"]),cmd) for i in reader if i["Name"][0:1] != "#"]
                for r in results:
                    print(r.result())
    t2=time.perf_counter()
    print(f"Finished after {t2-t1}")
    srcfile.close()
if __name__ == "__main__":
    main()
    