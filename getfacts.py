#!
#Name: Get and Find Configuration from Cisco IOS Devices
#Author: Tuan Hoang
#Version: 1.0
#
import warnings
#from urllib3.exceptions import NotOpenSSLWarning

warnings.filterwarnings("ignore")

import time, sys, datetime, csv, os

import click, json
from core.credentials import get_credentials
from core.executor import run_parallel
# from core.device import get_config, get_config_to_file
from core.utility import format_msg, print_result
from core.logging_manager import setup_loggers





def main():
    # success_logger, fail_logger = setup_loggers(logger_name="getconfig")
    list="inventory/devices.csv"
    username, password = get_credentials()
    try:
        srcfile = open(list, "rt")
        reader = csv.DictReader(srcfile)
    except Exception as e:
        print(f"{datetime.datetime.now()}: {e}")
        sys.exit(1)

    
    # # reinitialize reader
    # srcfile.seek(0)              
    # reader = csv.DictReader(srcfile)  
    cmds=[]

    # Choose run_func based on writefile
    run_func = (lambda retriever: retriever.get_host_info())

    results = run_parallel(
        reader,
        cmds,
        username,
        password,
        run_func=run_func,
        # success_logger=success_logger,
        # fail_logger=fail_logger,
        # debug=1,
        # filterlist=filterlist if filterlist else None,
        # outfolder=writefile if writefile else None,
        sanitizeconfig=False,
        # removepassword=removepasswords,
    )
    print(results)
    # Print results only if not writing to file

    # Time report
    # t2 = time.perf_counter()
    # print(format_msg(f"Finished after {t2 - t1}", "GREEN"))
    srcfile.close()

    # Git actions
    # if git:
    #     git_commit_and_push()  # commit + push
    # elif gitcommitonly:
    #     git_commit_and_push(push=False)  # commit only

if __name__ == '__main__':
    main()
