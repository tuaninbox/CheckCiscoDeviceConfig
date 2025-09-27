  
from napalm import get_network_driver
from core.utility import remove_password, write_log_to_file, write_fail_log_to_file
import traceback

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

def get_config(hostname,host,user,password,cmdlist):
    print(f"{bcolors.BLUE}Connecting to {hostname} - {host}{bcolors.ENDC}")
    try:
        driver=get_network_driver('ios')
        #This is for ssh connection
        device=driver(host,user,password)
        device.open()
        output =f"\n{bcolors.CYAN}{str(hostname)}  - {str(host)} Command Outputs:{bcolors.ENDC}\n"
        r=""
        if isinstance(cmdlist,list):
            for cmd in cmdlist:
                r=device.cli(commands=[cmd])
                output=output + "\n" + hostname + "# " + cmd + "\n" + remove_password(r[cmd])
        else:
            r=device.cli(commands=[cmdlist])
            output=output + "\n" + hostname + "# " + cmdlist + "\n" + remove_password(r[cmdlist])
        device.close()
        return output
    except:
        try:
            driver=get_network_driver('ios')
            #This is for telnet connection
            device=driver(host,user,password,optional_args={"transport":"telnet"})
            device.open()
            r=""
            if isinstance(cmdlist,list):
                for cmd in cmdlist:
                    r=device.cli(commands=[cmd])
                    output=output + "\n" + hostname + "# " + cmd + "\n" + remove_password(r[cmd])
            else:
                r=device.cli(commands=[cmdlist])    
                output=output + "\n" + hostname + "# " + cmd + "\n" + remove_password(r[cmdlist])
            device.close()
            return output
        except Exception as e:
            # traceback.print_exc()
            tb = traceback.extract_tb(sys.exc_info()[2])[0]  # Get last traceback entry
            line_number = tb.lineno
            filename = tb.filename
            failed_line = tb.line

            write_fail_log_to_file(e, f"{hostname}-{host} at {filename}:{line_number} → {failed_line}")
            return f"{bcolors.RED}{e} at line {line_number} in {filename} → {failed_line} for {hostname} - {host}{bcolors.ENDC}"
        # except:
        #     writefaillogtofile(sys.exc_info()[1],hostname+"-"+host)
        #     #return "Error: " + str(sys.exc_info()[1]) + " " + str(hostname) + " - " + str(host)
        #     return f"{bcolors.RED}{sys.exc_info()[1]} for {hostname} - {host}{bcolors.ENDC}"

def get_cmds(hostname,host,user,password,cmdlist):
    print(f"Connecting to {hostname} - {host}")
    try:
        driver=get_network_driver('ios')
        #This is for ssh connection
        device=driver(host,user,password)
        device.open()
        output = str(hostname) + " - " + str(host) + " Command Outputs:\n"    
        for cmd in cmdlist:
            r=device.cli(commands=[cmd])
            output=output + "\n" + hostname + "# " + cmd + "\n" + removepassword(r[cmd])
        device.close()
        return output
    except:
        try:
            #print("Trying telnet")
            driver=get_network_driver('ios')
            #This is for telnet connection
            device=driver(host,user,password,optional_args={"transport":"telnet"})
            device.open()
            r=""
            for cmd in cmdlist:
                r = r + device.cli(commands=[cmd])
            device.close()
            return str(hostname) + " - " + str(host) + " Configuration:\n" + removepassword(r[cmd]) 
        except:
            write_fail_log_to_file(sys.exc_info()[1],hostname+"-"+host)
            #return "Error: " + str(sys.exc_info()[1]) + " " + str(hostname) + " - " + str(host)
            return f"{bcolors.RED}{sys.exc_info()[1]} for site {hostname} - {host}{bcolors.ENDC}"


#function write config to file
def get_config_to_file(hostname,host,user,password,cmd,outfolder):
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

def getcmdstofile(hostname,host,user,password,cmdlist,outfolder,group=""):
    try:
        output=getcmds(hostname,host,user,password,cmdlist)
        x=re.search("^.*timed out for site",output)
        #x=re.search("^.*onfiguration:",output)
        if not x:
            if group=="":
                outfile=str(outfolder)+"/"+hostname+".txt"
            else:
                outfile=str(outfolder)+"/"+str(group)+"/"+hostname+".txt"
            if not os.path.exists(outfolder+"/"+str(group)):
                os.makedirs(outfolder+"/"+str(group))
            fp=open(outfile,"w")
            fp.write(output)
            fp.close()
            #success
            return f"{bcolors.BLUE}Configuration of {hostname} - {host} saved in {outfile}{bcolors.ENDC}"
        else:
            return f"{bcolors.RED} {output} {bcolors.ENDC}"
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