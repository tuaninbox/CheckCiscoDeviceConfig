import re, os, sys, datetime


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

def format_msg(msg,color=""):
    if color == "":
        return f"{msg}"
    else:
        return f"{getattr(bcolors,color)}{msg}{bcolors.ENDC}"
    
def print_result(result, colorize=True,debug=0):
    if result["success"]:
        header = format_msg(f"{result['hostname']} - {result['host']}", "CYAN") if colorize else f"{result['hostname']} - {result['host']}"
        print(header)
        print(result["output"])
    else:
        err = result["error"]
        msg = f"{result['hostname']} - {result['host']} - {err['message']} at {err['filename']}: {err['line']} - {err['code']}" if debug else f"{result['hostname']} - {result['host']} - {err['message']}"
        print(format_msg(msg, "RED") if colorize else msg)


# #function write log to file
# def write_fail_log_to_file(msg, hostname):
#     try:
#         logging.info(f"{hostname} - {msg}")
#     except Exception as e:
#         print(f"Logging error: {e}")

# #function write log to file
# def write_log_to_file(config,filename,group,date):
#     try:
#         outfolder="./"+group+"/"+str(date)
#         outfile=outfolder+"/searchresult.log"
#         logging.basicConfig(filename=outfile,level=logging.INFO)
#         if not os.path.exists(outfolder):
#                 os.makedirs(outfolder)
#         logging.info(config)
#         #success
#         return "Finish checking site {}. Log saved in {}".format(filename,outfile)
#     except:
#         return "Write log to file error {0}".format(sys.exc_info()[1])
#         #failure
#         #return 0


# def write_search_output_to_file(output,outfolder):
#     try:
#         #outfolder="./"+outfolder+"/"+str(datetime.datetime.now().date())
#         outfile=str(outfolder)+"/"+str(searchstring)+"output.txt"
#         #if not os.path.exists(outfolder):
#         #       os.makedirs(outfolder)
#         if not os.path.exists(outfile):
#             open(outfile,"w").close()
#         fp=open(outfile,"a")
#         fp.write(output+"\n")
#         fp.close()
#         #success
#         return "Output of site {} - {} saved in {}".format(hostname,host,outfile)
#     except:
#         return "Write output to file error {} for site {} - {}".format(sys.exc_info()[1],hostname,host)
#         #failure
#         #return 0