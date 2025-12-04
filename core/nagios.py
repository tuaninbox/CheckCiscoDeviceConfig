import requests
import csv
from core.credentials import get_nagios_api

nagios_host, nagios_apikey = get_nagios_api()

def get_hostgroup_members_from_nagios(hostgroup_name):
    url = f"https://{nagios_host}/nagiosxi/api/v1/config/hostgroups?pretty=1&apikey={nagios_apikey}&hostgroup_name={hostgroup_name}"
    r = requests.get(url, verify=False)
    return r.json().get("members", [])

def get_device_list_from_nagios(nagios_host=nagios_host, nagios_apikey=nagios_apikey):
    # Define the hostgroups you want to query
    hostgroups = ["ConfigBackup_ios", "ConfigBackup_nxos"]

    # Build a dict mapping device -> OS
    backup_device_dict = {}
    for hg in hostgroups:
        os_type = hg.replace("ConfigBackup_", "").lower()
        members = get_hostgroup_members_from_nagios(hg)
        for device in members:
            backup_device_dict[device.lower()] = os_type

    # Query all Nagios hosts
    url = f"https://{nagios_host}/nagiosxi/api/v1/config/host?pretty=1&apikey={nagios_apikey}&orderby=host_name:a"
    r = requests.get(url, verify=False)
    devices = r.json()

    results = []
    for d in devices:
        host_name = d.get("host_name", "").lower()
        if host_name in backup_device_dict:
            results.append({
                "Host": d.get("host_name", ""),
                "IP": d.get("address", ""),
                "Port": "",
                "Location": d.get("alias", ""),
                "Group": d.get("hostgroup_name", ""),
                "OS": backup_device_dict[host_name]  # Add OS info
            })

    # Optional: write results to CSV
    with open("backup_devices.csv", "w", newline="") as csvfile:
        fieldnames = ["Host", "IP", "Port", "Location", "Group", "OS"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    return results

if __name__ == "__main__":
    results = get_device_list_from_nagios()
    print(results)






# import requests
# from pathlib import Path
# from core.logging_manager import setup_loggers
# # import configparser
# from core.credentials import get_nagios_api
# # Initialize loggers for this module
# # success_logger, fail_logger = setup_loggers(logger_name="nagios")

# nagios_host, nagios_apikey = get_nagios_api()

# def get_device_list_from_nagios(nagios_host=nagios_host, nagios_apikey=nagios_apikey):
#     backup_device_list = [device.lower(0 for device in get_hostgroup_members_from_naigos("ConfigBackup")]
#     url = f"https://{nagios_host}/nagiosxi/api/v1/config/host?pretty=1&apikey={nagios_apikey}&orderby=host_name:a"
#     r = requests.get(url,verify=False)
#     devices = r.json()
#     results = []
#     for d in devices:
#         host_name = d.get("host_name", "").lower()
#         if host_name in backup_device_list:
#             results.append({
#                 "Host": d.get("host_name", ""),
#                 "IP": d.get("address", ""),          # Nagios JSON usually has 'address'
#                 "Port": "",                          # Leave empty
#                 "Location": d.get("alias", ""),      # Often 'alias' or custom field
#                 "Group": d.get("hostgroup_name", "") # Adjust if Nagios returns differently
#             })

#     # Write results to CSV
#     with open("backup_devices.csv", "w", newline="") as csvfile:
#         fieldnames = ["Host", "IP", "Port", "Location", "Group"]
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(results)

#     return results
#     return results

# def get_hostgroup_members_from_naigos(hostgroup_name):
#     url = f"https://{nagios_host}/nagiosxi/api/v1/config/hostgruops?pretty=1&apikey={nagios_apikey}&hostgroup_name={hostgroup_name}"
#     r = requests.get(url,verify=False)
#     return r.json()["members"]
    
# if __name__ == "__main__":
#     results = get_device_list_from_nagios()
#     print(results)