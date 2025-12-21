import csv
import yaml
import os
from netmiko import ConnectHandler
from jinja2 import Template
from core.credentials import get_credentials
from core.logging_manager import setup_loggers

configuration_folder="configuration"
OS_MAP = {
    "iosxe": "cisco_ios",
    "ios": "cisco_ios",
    "nxos": "cisco_nxos",
    "nxos_ssh": "cisco_nxos",
    "nxos_nxapi": "cisco_nxos_nxapi",
}

success_logger, fail_logger = setup_loggers(logger_name="configuredevices")
username, password = get_credentials()
# Load inventory
devices = []
with open("inventory/devices.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["Host"].startswith("#"):   # skip commented lines
            continue
        devices.append(row)

for dev in devices:
    group = dev.get("Group", "").strip().lower() or "default"

    # Build template and variable file names
    template_file = f"{configuration_folder}/{group}_template.j2"
    vars_file = f"{configuration_folder}/{group}_vars.yml"

    if not os.path.exists(template_file):
        template_file = f"{configuration_folder}/default_template.j2"
        vars_file = f"{configuration_folder}/default_vars.yml"

    # Load template
    with open(template_file) as f:
        template = Template(f.read())

    # Load group variables
    try:
        with open(vars_file) as f:
            group_vars = yaml.safe_load(f)
    except FileNotFoundError:
        group_vars = {}

    # Merge CSV row values with group variables
    context = {**dev, **group_vars}

    # Render template
    config = template.render(context)
    config_commands = config.strip().splitlines()
    
    # Build Netmiko connection dict
    device_params = {
        "device_type": OS_MAP.get(dev["OS"].lower()),
        "host": dev["IP"],
        "username": username,
        "password": password,
        "secret": "enablepass",
    }

    net_connect = ConnectHandler(**device_params)
    net_connect.enable()
    print(f"Configuring {dev['Host']} ({dev['IP']}) with {template_file}...")
    output = net_connect.send_config_set(config_commands)
    print(f"output: {output}")

    # --- NEW: Post-check logic ---
    checks = context.get("verification", [])
    success = True
    for check in checks:
        cmd = check.get("command")
        expect = check.get("expect")
        if not cmd or not expect:
            continue
        result = net_connect.send_command(cmd)
        print(f"result: {result}")
        if expect not in result:
            print(f"❌ Check failed: {cmd} (expected '{expect}')")
            success = False
        else:
            print(f"✅ Check passed: {cmd}")

    if success:
        net_connect.save_config()
        print(f"✔ Success: {dev['Host']} configuration saved.")
    else:
        print(f"✖ Failure: {dev['Host']} configuration NOT saved.")

    net_connect.disconnect()
