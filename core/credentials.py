import os, getpass, configparser

from core.logging_manager import setup_loggers
from config.config_loader import load_account_config, load_nagios_config

# Initialize loggers for this module
success_logger, fail_logger = setup_loggers(logger_name="credential")


def get_credentials():
    username = None
    password = None

    # Expand ~ to full path
    filename = os.path.expanduser(load_account_config())

    # 1. Try reading from credential file using configparser
    if os.path.exists(filename):
        config = configparser.ConfigParser()
        config.read(filename)

        if "credentials" in config:
            username = config["credentials"].get("username")
            password = config["credentials"].get("password")

    # 2. Fall back to environment variables
    if not username:
        username = os.environ.get("username")
    if not password:
        password = os.environ.get("password")

    # 3. Prompt user if still missing
    if not username:
        username = input("Enter username: ")
    if not password:
        password = getpass.getpass("Enter password: ")

    return username, password

def get_nagios_api():
    nagios_host = None
    nagios_apikey = None

    # Expand ~ to full path
    filename = os.path.expanduser(load_nagios_config())

    # 1. Try reading from credential file using configparser
    if os.path.exists(filename):
        config = configparser.ConfigParser()
        config.read(filename)

        if "nagios" in config:
            nagios_host = config["nagios"].get("nagios_host")
            nagios_apikey = config["nagios"].get("nagios_apikey")

    # 2. Fall back to environment variables
    if not nagios_host:
        nagios_host = os.environ.get("nagios_host")
    if not nagios_apikey:
        nagios_apikey = os.environ.get("nagios_apikey")

    # 3. Prompt user if still missing
    if not nagios_host:
        nagios_host = input("Enter Nagios Host: ")
    if not password:
        nagios_apikey = getpass.getpass("Enter Nagios APIKey: ")

    return nagios_host, nagios_apikey

if __name__=="__main__":
    print(get_credentials())