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
from core.device import startinteractivesession, load_commands


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

def main(ctx, find, list, device, writefile, command, commandfile, interactive):
    success_logger, fail_logger = setup_loggers(logger_name="getconfig")

    # Show help if no options
    if not any([find, list, device, writefile, command, commandfile]):
        click.echo(ctx.get_help())
        ctx.exit()
        
    # If only device list is provided, but no command/interactive/find, show usage
    if list and not any([command, commandfile, interactive, find, device, writefile]):
        click.echo("You must provide a command (-c or -cf), or use interactive mode (-i).")
        click.echo(ctx.get_help())
        ctx.exit()

    # Exclusive options check
    exclusive = [command, commandfile, interactive]
    if sum(bool(x) for x in exclusive) > 1:
        raise click.UsageError("Only one of --command, --commandfile, or --interactive can be used.")

    username, password = get_credentials()
    try:
        srcfile = open(list, "rt")
        reader = csv.DictReader(srcfile)
    except Exception as e:
        print(f"{datetime.datetime.now()}: {e}")
        sys.exit(1)


    # Interactive mode - GOOD
    if interactive:
        for row in reader:
            if row["Host"] == str(device):  # assuming 'site' == 'device'
                startinteractivesession(
                    row["Host"],
                    row["IP"],
                    username,
                    password
                    # username if not row["Username"] else row["Username"],
                    # password if not row["Password"] else row["Password"],
                )
        srcfile.close()
        return
    
    # Build command list
    # cmds = command if command else open(commandfile, "rt").readlines()
    if command:
        cmds = [command]
    elif commandfile:
        cmds=load_commands(commandfile)
    else:
        raise click.UsageError("You must provide --command or --commandfile unless using --interactive.")

    # print(cmds)
    findstring = str(find) if find else None

    t1 = time.perf_counter()

    # Non-interactive mode
    # Build filterlist if device specified
    filterlist = []

    # reinitialize reader
    srcfile.seek(0)              
    reader = csv.DictReader(srcfile)  
    if device and not find:
        filterlist = [device for r in reader if str(device) == r["Host"]]
        if not filterlist:
            print(format_msg(f"{device} is not in inventory", "YELLOW"))
            srcfile.close()
            return
        # Reset reader for run_parallel
        srcfile.seek(0)
        reader = csv.DictReader(srcfile)

    # Choose run_func based on writefile
    run_func = (lambda retriever: retriever.get_config_to_file()) if writefile else (lambda retriever: retriever.get_config())

    results = run_parallel(
        reader,
        cmds,
        username,
        password,
        run_func=run_func,
        success_logger=success_logger,
        fail_logger=fail_logger,
        debug=1,
        filterlist=filterlist if filterlist else None,
        outfolder=writefile if writefile else None,
    )
    # print(results)
    # Print results only if not writing to file
    if not writefile:
        for r in results:
            print_result(r)

    # Time report
    t2 = time.perf_counter()
    print(format_msg(f"Finished after {t2 - t1}", "GREEN"))
    srcfile.close()

if __name__ == '__main__':
    main()
    # commandfile = "cmd.txt"
    # commands_json = load_commands(commandfile)
    # print(json.dumps(commands_json, indent=2))
    # for c in commands_json["ios"]:
    #     print(c)