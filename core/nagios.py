import requests
from pathlib import Path
from core.logging_manager import setup_loggers
import configparser
from core.credentials import get_nagios_api
# Initialize loggers for this module
# success_logger, fail_logger = setup_loggers(logger_name="nagios")

# try:
#     # Read backup_dir from gitrepo.ini
#     config = configparser.ConfigParser()
#     config.read("config/config.ini")
#     backup_dir = Path(config["gitrepo"]["backup_dir"]).expanduser()
# except KeyError:
#     fail_logger.error("Missing 'backup_dir' in config.ini under [gitrepo] section or configfile does not exist")
#     raise

nagios_host, nagios_apikey = get_nagios_api()

def get_device_list_from_nagios(nagios_host=nagios_host, nagios_apikey=nagios_apikey):
    url = f"https://{nagios_host}/nagiosxi/api/v1/config/host?pretty=1&apikey={nagios_apikey}&orderby=host_name:a"
    r = requests.get(url,verify=False)
    devices = r.json()
    results = []
    for r in results:
        results.append(r['host_name'].upper())
    return results

if __name__ == "__main__":
    results = get_device_list_from_nagios()
    print(results)