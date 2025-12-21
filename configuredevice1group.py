import csv, sys
from netmiko import ConnectHandler
from jinja2 import Template

# Load inventory
devices_by_group = {}
with open("inventory/devices.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # skip commented lines
        if row["Host"].startswith("#"):
            continue
        group = row["Group"]
        devices_by_group.setdefault(group, []).append(row)

# Pick a group
group_name = "lab"
devices = devices_by_group.get(group_name, [])
print(devices)
sys.exit(0)
# Load config template
with open("router_config.j2") as f:
    template = Template(f.read())

for dev in devices:
    # Render template with row variables
    config = template.render(dev)
    config_commands = config.strip().splitlines()

    # Build Netmiko connection dict
    device_params = {
        "device_type": dev["OS"],   # map to netmiko type if needed
        "host": dev["IP"],
        "username": "admin",        # could also come from CSV
        "password": "password123",
        "secret": "enablepass",
    }

    net_connect = ConnectHandler(**device_params)
    net_connect.enable()
    print(f"Configuring {dev['Host']} ({dev['IP']})...")
    output = net_connect.send_config_set(config_commands)
    print(output)
    net_connect.save_config()
    net_connect.disconnect()
