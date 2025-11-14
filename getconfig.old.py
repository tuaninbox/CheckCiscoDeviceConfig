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
@click.option('-s', '--site', type=str, help='Site to run command')
@click.option('-w', '--writefile', type=str, help='Write to File')
@click.option('-c', '--command', type=str, help='Command to run')
@click.option('-cf', '--commandfile', type=str, help='File contains commands to run')
@click.option('-i', '--interactive', is_flag=True, help='Interactive Session')
@click.pass_context
def main(ctx,find, list, site, writefile, command, commandfile, interactive):
    # Call this once during initialization
    success_logger, fail_logger = setup_loggers()

    # If no options are provided, show help
    if not any([find, list, site, writefile, command, commandfile]):
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
        if site and find: #find keyword from command on 1 site
            # print("find command in one site")
            for i in reader:
                # if i["Name"] == str(args.site):
                if i["Name"] == str(site):
                    result=searchconfig(i["Name"],i["Host"],username if i["Username"] == "" else i["Username"],
                            password if i["Password"] == "" else i["Password"],cmd,findstring,writefile)
                    #outfile=str(args.writefile)+"/"+i["Name"]+"output.txt"
                    outfile=str(writefile)+"/"+i["Name"]+"output.txt"
                    with open(outfile,'w') as file:
                        print("Output of site {} - {} saved in {}".format(hostname,host,outfile))
                        file.write(r.result())   
        elif not site and find: #find keyword from command on all sites
            # print("find command in all sites")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results=[executor.submit(searchconfig,i["Name"],i["Host"],username if i["Username"] == "" else i["Username"],
                            password if i["Password"] == "" else i["Password"],cmd,findstring) for i in reader if i['Name'][0:1] != "#"]
                outfile=str(writefile)+"/"+"find output.txt "
                print("Search Result is being saved in {}".format(outfile))
                with open(outfile,'w') as file:
                    for r in results:
                        print(".")
                        file.write(r.result()+"\n")   
        elif site and not find: #run command on 1 site
            # print( "get config from one site")
            for i in reader:
                if i["Name"] == str(site):
                    print(getconfigtofile(i["Name"],i["Host"],username if i["Username"] == "" else i["Username"],
                            password if i["Password"] == "" else i["Password"],cmd,writefile))
        elif not site and commandfile: # run command list for all sites
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results=[executor.submit(getcmdstofile,i["Name"],i["Host"],username if i["Username"] == "" else i["Username"],
                            password if i["Password"] == "" else i["Password"],cmd,writefile,i["Group"]) for i in reader if i["Name"][0:1] != "#"]
                for r in results:
                    print(r.result())
##### GOOD #####
        else:# not args.site and not args.find: run command from all sites
            if writefile: #write to file
                results=run_parallel(reader, cmd, username, password, get_config_to_file,outfolder=writefile)
            for r in results:
                # print(r.result())
                print(r)
    else: #non-interactive mode -c, write to stdout, without -w
        if site: # run command on 1 site
            # print( "get config from one site")
            for i in reader:
                # if i["Name"] == str(args.site):
                if i["Name"] == str(site):
                    print(getconfig(i["Name"],i["Host"],username if i["Username"] == "" else i["Username"],
                            password if i["Password"] == "" else i["Password"],cmd))
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
                    
##### GOOD #####
        else:# not args.site and not args.find: run command on all sites
            # results=run_parallel(reader, cmd, username, password, get_config, success_logger=success_logger, fail_logger=fail_logger, debug=1)
            # # print("get config from all sites")         
            # for r in results:
            #     print_result(r)
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
                print_result(r)
    t2=time.perf_counter()
    print(format_msg(f"Finished after {t2-t1}","GREEN"))
    srcfile.close()


if __name__ == "__main__":
    main()