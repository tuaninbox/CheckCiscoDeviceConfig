#!
#Name: Get and Find Configuration from Cisco IOS Devices
#Author: Tuan Hoang
#Version: 1.0
#
import warnings
#from urllib3.exceptions import NotOpenSSLWarning

warnings.filterwarnings("ignore")

import time, sys, datetime, csv, os

import click
from core.credentials import get_credentials
from core.executor import run_parallel
# from core.device import get_config, get_config_to_file
from core.utility import format_msg, print_result
from core.logging_manager import setup_loggers



# Main function with Click menu
@click.command(
    context_settings=dict(help_option_names=['-h', '--help']),
    help="Get Configuration: Run commands on devices, search output, or save results.")
@click.option('-f', '--find', type=str, help='Keyword to find')
@click.option('-l', '--list', type=str, required=False, help='Device List File')
@click.option('-d', '--device', type=str, help='Site to run command')
@click.option('-w', '--writefile', type=str, help='Write to File')
@click.option('-c', '--command', type=str, help='Command to run')
@click.option('-cf', '--commandfile', type=str, help='File contains commands to run')
@click.option('-i', '--interactive', is_flag=True, help='Interactive Session')
@click.pass_context
def main(ctx,find, list, device, writefile, command, commandfile, interactive):
    # Call this once during initialization
    success_logger, fail_logger = setup_loggers(logger_name="getconfig")

    # If no options are provided, show help
    if not any([find, list, device, writefile, command, commandfile]):
        click.echo(ctx.get_help())
        ctx.exit()

    # Some options are exclusive
    exclusive = [command, commandfile, interactive]
    if sum(bool(x) for x in exclusive) > 1:
        raise click.UsageError("Only one of --command, --commandfile, or --interactive can be used.")

    username, password = get_credentials()
    try:
        #Read devices file
        csvfile=list
        srcfile = open(csvfile,"rt")
        reader = csv.DictReader(srcfile)
    except:
        msg = str(datetime.datetime.now())+": "+str(sys.exc_info()[1])
        print(msg)
        sys.exit(1)

    #if args.command:
    if command:
        #cmd = str(args.command)
        cmd = str(command)
    else:
        #with open(args.commandfile,'rt') as f:
        with open(commandfile,'rt') as f:
            cmd = f.readlines()
       
    #findstring = str(args.find)
    findstring = str(find)
    t1=time.perf_counter()
    #if args.interactive: # interactive mode -i, can't use with -c
    if interactive: # interactive mode -i, can't use with -c
        for i in reader:
            # if i["Name"] == str(args.site):
            if i["Name"] == str(site):
                startinteractivesession(i["Name"],i["Host"],username if i["Username"] == "" else i["Username"],
                            password if i["Password"] == "" else i["Password"],)
    elif writefile: #non-interactive mode -c, write to file -w <folder>
        if device and not find: #run command on 1 site
            filterlist=[]
            filterlist=[device for r in reader if str(device) == r["Name"]]
            if len(filterlist) == 0:
                print(format_msg(f"{device} is not in inventory","YELLOW"))
            else:
                srcfile.seek(0)
                reader = csv.DictReader(srcfile)
                results=run_parallel(
                    reader, 
                    cmd, 
                    username, 
                    password, 
                    run_func= lambda retriever: retriever.get_config_to_file(),
                    success_logger=success_logger,
                    fail_logger=fail_logger,
                    debug=1,
                    filterlist=filterlist,
                    outfolder=writefile)
                
                # for r in results:
                #     print(r)
                                

##### GOOD - Run command on all devices - Save to file #####
        else:# not args.site and not args.find: run command from all sites
            if writefile: #write to file
                # from config.logging_config import LOGGING_CONFIG
                # LOGGING_CONFIG["console"] = True
                # success_logger, fail_logger = setup_loggers(logger_name="getconfig")
                results=run_parallel(
                    reader, 
                    cmd, 
                    username, 
                    password, 
                    run_func= lambda retriever: retriever.get_config_to_file(),
                    success_logger=success_logger,
                    fail_logger=fail_logger,
                    debug=1,
                    outfolder=writefile)
            # for r in results:
            #     print(r)
        
# Non-interactive                
    else: #non-interactive mode -c, write to stdout, without -w
##### GOOD - Run Command on 1 device #####
        # elif args.site and not args.find: # run command on 1 site
        if device and not find: # run command on 1 site
            filterlist=[]
            filterlist=[device for r in reader if str(device) == r["Name"]]
            if len(filterlist) == 0:
                print(format_msg(f"{device} is not in inventory","YELLOW"))
            else:
                srcfile.seek(0)
                reader = csv.DictReader(srcfile)
                results = run_parallel(
                    reader,
                    cmd,
                    username,
                    password,
                    run_func=lambda retriever: retriever.get_config(),
                    success_logger=success_logger,
                    fail_logger=fail_logger,
                    debug=1,
                    filterlist=filterlist
                    )
                
                # for r in results:
                #     # Print json dict
                #     # print(r)
                #     # Print plain text output
                #     print_result(r)
##### GOOD - Run Command on all devices #####
        else:# not args.site and not args.find: run command on all sites
            # results=run_parallel(reader, cmd, username, password, get_config, success_logger=success_logger, fail_logger=fail_logger, debug=1)
            # # print("get config from all sites")         
            # for r in results:
            #     print_result(r)
            # Turn console logging ON
            # from config.logging_config import LOGGING_CONFIG
            # LOGGING_CONFIG["console"] = True
            # success_logger, fail_logger = setup_loggers()
            results = run_parallel(
                reader,
                cmd,
                username,
                password,
                run_func=lambda retriever: retriever.get_config(),
                success_logger=success_logger,
                fail_logger=fail_logger,
                debug=1
                )
            
            for r in results:
                # Print json dict
                # print(r)
                # Print plain text output
                print_result(r)
    
# Print Time Report
    t2=time.perf_counter()
    print(format_msg(f"Finished after {t2-t1}","GREEN"))
    srcfile.close()


if __name__ == "__main__":
    main()