#!
#Name: Get and Find Configuration from Cisco IOS Devices
#Author: Tuan Hoang
#Version: 1.0
#
import warnings
#from urllib3.exceptions import NotOpenSSLWarning

warnings.filterwarnings("ignore")

import time, sys, datetime, csv, os

import click, json, yaml
from core.credentials import get_credentials
from core.executor import run_parallel
# from core.device import get_config, get_config_to_file
from core.utility import format_msg, print_csv, print_table
from core.logging_manager import setup_loggers


@click.command(
    context_settings=dict(help_option_names=['-h', '--help']),
    help="Get Configuration: Run commands on devices, search output, or save results.")
@click.option('-l', '--list', type=str, required=False, help='Device List File')
@click.option('-d', '--device', type=str, help='Site to run command')
@click.option('-cf', '--commandfile', type=str, help='File contains commands to run')
@click.pass_context

def main(ctx, list, device, commandfile):

    # Show help if no options
    if not any([list, device, commandfile]):
        click.echo(ctx.get_help())
        ctx.exit()
        
    success_logger, fail_logger = setup_loggers(logger_name="configuration")

    username, password = get_credentials()
    try:
        srcfile = open(list, "rt")
        reader = csv.DictReader(srcfile)
    except Exception as e:
        print(f"{datetime.datetime.now()}: {e}")
        sys.exit(1)

    if commandfile:
        # Load YAML once
        yaml_cmds = yaml.safe_load(open(commandfile))
    else:
        raise click.UsageError(
            "You must provide --command or --commandfile unless using --interactive."
        )


    t1 = time.perf_counter()

    # Filterlist logic
    filterlist = []
    srcfile.seek(0)
    reader = csv.DictReader(srcfile)

    if device:
        filterlist = [device.lower() for r in reader if str(device).lower() == r["Host"].lower()]
        if not filterlist:
            print(format_msg(f"{device} is not in inventory", "YELLOW"))
            srcfile.close()
            return
        srcfile.seek(0)
        reader = csv.DictReader(srcfile)

    # run_func for configuration 
    run_func = lambda obj: obj.apply_config()

    # Call run_parallel
    results = run_parallel(
        reader,
        yaml_cmds,
        username,
        password,
        run_func=run_func,
        mode="configure",          
        success_logger=success_logger,
        fail_logger=fail_logger,
        debug=1,
        filterlist=filterlist if filterlist else None,
        outfolder=None,
        sanitizeconfig=False,
        removepassword=False
    )



    columns = ["device", "address", "status", "details"]
    success_list = [r for r in results if r.get("status") == "success"]
    failed_list  = [r for r in results if r.get("status") == "failed"]

    # print_table("Success", success_list, columns)
    # print_table("Failed", failed_list, columns)
    
    print_csv("Success", success_list, columns)
    print_csv("Failed", failed_list, columns)


    # Time report
    t2 = time.perf_counter()
    print(format_msg(f"Finished after {t2 - t1}", "GREEN"))
    srcfile.close()


if __name__ == '__main__':
    main()

