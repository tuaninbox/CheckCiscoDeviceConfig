#!
#Name: Get and Find Configuration from Cisco IOS Devices
#Author: Tuan Hoang
#Version: 1.0
#
import warnings
warnings.filterwarnings("ignore")

import time, sys, datetime, csv, os
import click, json

from core.credentials import get_credentials
from core.executor import run_parallel
from core.utility.utility import format_msg, print_result
from core.logging_manager import setup_loggers


def main():
    # success_logger, fail_logger = setup_loggers(logger_name="getconfig")
    listfile = "inventory/devices.csv"
    username, password = get_credentials()

    try:
        srcfile = open(listfile, "rt")
        reader = csv.DictReader(srcfile)
    except Exception as e:
        print(f"{datetime.datetime.now()}: {e}")
        sys.exit(1)

    cmds = []  # command list per OS type if needed

    # Run inventory collector
    results = run_parallel(
        reader,
        cmds,
        username,
        password,
        collector_type="inventory",   # <-- new explicit flag
    )

    print(json.dumps(results, indent=2))

    srcfile.close()


if __name__ == '__main__':
    main()
