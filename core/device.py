import os
import sys, re
import traceback
from napalm import get_network_driver
import subprocess, shutil
import configparser
from core.utility import format_msg

import configparser
from pathlib import Path

def sanitize_config(raw_output: str, os_name: str, command: str, config_file: str = "config/commandfilters.ini") -> str:
    """
    Sanitize CLI output based on OS and command rules.
    Filters are read directly from filters.ini.
    
    Args:
        raw_output (str): Raw CLI output from device.
        os_name (str): Operating system name (e.g., "nxos", "ios", "asa").
        command (str): Command string (e.g., "show running-config").
        config_file (str): Path to filters.ini file.
    
    Returns:
        str: Sanitized output with volatile lines removed.
    """
    if not os.path.exists(config_file):
        print(f"Config file not found: {config_file}")
        # Return raw output unchanged if no config file
        exit()

    cfg = configparser.ConfigParser()
    cfg.read(config_file)

    section = f"{os_name}:{command}"
    rules = {
        "prefix": [],
        "contains": []
    }

    if cfg.has_section(section):
        rules["prefix"] = [s.strip() for s in cfg.get(section, "exclude_prefix", fallback="").split(",") if s.strip()]
        rules["contains"] = [s.strip() for s in cfg.get(section, "exclude_contains", fallback="").split(",") if s.strip()]

    sanitized_lines = []
    for line in raw_output.splitlines():
        stripped = line.strip()  # remove leading/trailing spaces
        lower = stripped.lower() # normalize case

        # Skip if matches prefix
        if any(lower.startswith(p.lower()) for p in rules["prefix"]):
            continue
        # Skip if contains substring
        if any(c.lower() in lower for c in rules["contains"]):
            continue

        sanitized_lines.append(line)

    return "\n".join(sanitized_lines).strip()+ "\n"


def sanitize_configold(raw_output: str, os_name: str, command: str, config_file: str = "commandfilters.ini") -> str:
    """
    Sanitize CLI output based on OS and command rules using regex filters.
    """
    cfg = configparser.ConfigParser()
    cfg.read(config_file)

    section = f"{os_name}:{command}"
    regex_patterns = []

    if cfg.has_section(section):
        regex_patterns = [
            re.compile(p.strip(), re.IGNORECASE)
            for p in cfg.get(section, "exclude_regex", fallback="").split(",")
            if p.strip()
        ]

    sanitized_lines = []
    for line in raw_output.splitlines():
        stripped = line.strip()
        # Skip if any regex matches
        if any(pattern.search(stripped) for pattern in regex_patterns):
            continue
        sanitized_lines.append(line)

    return "\n".join(sanitized_lines)

class DeviceDataRetriever:
    def __init__(self, hostname, host, os, user, password, cmdlist, success_logger=None, fail_logger=None, debug=0, outfolder="output", sanitizeconfig=True):
        self.hostname = hostname
        self.host = host
        self.os = os
        self.user = user
        self.password = password
        self.cmdlist = cmdlist
        self.success_logger = success_logger
        self.fail_logger = fail_logger
        self.debug = debug
        self.outfolder = outfolder
        self.sanitizeconfig = sanitizeconfig
        self.result = {
            "hostname": hostname,
            "host": host,
            "success": False,
            "output": "",
            "error": None
        }

    def _run_session(self, optional_args=None, removepassword: int = 0):
        driver="ios"
        if self.os == "nxos":
            driver = "nxos_ssh"
        driver = get_network_driver(driver)
        device = driver(self.host, self.user, self.password, optional_args=optional_args or {})
        device.open()

        sanitizer = SecretSanitizer()   # instantiate once
        # print(self.cmdlist)
        commands = self.cmdlist if isinstance(self.cmdlist, list) else [self.cmdlist]
        # print(commands)
        output_lines = []
        for cmd in commands:
            r = device.cli([cmd])
            raw_output = r[cmd]
            if self.sanitizeconfig:
                clean_config = sanitize_config(raw_output,self.os,cmd)
            else:
                clean_config = raw_output
            sanitized_output = sanitizer.apply(clean_config, removepassword)
            output_lines.append(f"{self.hostname}# {cmd}\n{sanitized_output}")
            # output_lines.append(f"{self.hostname}# {cmd}\n{remove_password(r[cmd])}")

        device.close()
        self.result["success"] = True
        self.result["output"] = "\n".join(output_lines)
        if self.success_logger:
            self.success_logger.info(f"{self.hostname} - {self.host} - Configuration retrieved successfully")
        return self.result

    def get_config(self):
        try:
            return self._run_session(removepassword=1|2|4|8)
        # except:
        #     try:
        #         return self._run_session(optional_args={"transport": "telnet"})
        except Exception as e:
            tb = traceback.extract_tb(sys.exc_info()[2])[0]
            self.result["success"]= False
            self.result["error"] = {
                "message": str(e),
                "filename": tb.filename,
                "line": tb.lineno,
                "code": tb.line
            }
            fail_msg = f"{e} at {tb.filename}:{tb.lineno} - {tb.line}" if self.debug else e
            if self.fail_logger:
                self.fail_logger.error(f"{self.hostname} - {self.host} - {fail_msg}")
            return self.result

    def get_config_to_file(self, tolowercase=True):
        try:
            output = self.get_config()
            # print(type(output["success"]),output["success"])
            if output["success"]:
                outfolder = self.outfolder
                if tolowercase:
                    outfile = os.path.join(outfolder, f"{self.hostname.lower()}")
                else:
                    outfile = os.path.join(outfolder, f"{self.hostname}")
                if not os.path.exists(outfolder):
                    os.makedirs(outfolder)
                with open(outfile, "w") as fp:
                    fp.write(output["output"])
                return format_msg(f"Configuration of {self.hostname} - {self.host} saved in {outfile}","BLUE")
            else:
                # result["message"]=f"Can't get command output from devices {self.hostname} - {self.host}"
                fail_msg= f"{output['error']['message']} at {output['error']['filename']}: {output['error']['line']} - {output['error']['code']}" if self.debug else f"{output['error']['message']}"
                return format_msg(f"{self.hostname} - {self.host} - {fail_msg}","RED")
                # return format_msg(f"Can't get command output from devices {self.hostname} - {self.host}","RED")
        except:
            # result["message"]=f"Write configuration to file error {sys.exc_info()[1]} for site {self.hostname} - {self.host}"
            return format_msg(f"Write configuration to file error {sys.exc_info()[1]} for site {self.hostname} - {self.host}","RED")
        
class SecretSanitizer:
    def __init__(self):
        # Map bitmask values to methods
        self.removers = {
            1: self.remove_userpass,
            2: self.remove_snmp,
            4: self.remove_tacacs,
            8: self.remove_app_hosting,
        }

    def remove_userpass(self, configuration: str) -> str:
        # Example: strip generic username configs
        ret=re.sub(r'enable (secret|password) (\d)?.*','enable \g<1> \g<2> <removed>',configuration)
        ret=re.sub(r'(username\s+\S+\s+privilege\s+(?:[0-9]|1[0-5])\s+secret\s+[1-9])\s+\S+','\g<1> <removed>',ret)
        ret = re.sub(r'(username\s+\S+\s+password\s+\d+)\s+\S+','\g<1> <removed>',ret)
        return ret

    def remove_snmp(self, configuration: str) -> str:
        ret = re.sub(r'snmp-server community \b\w*',
                     'snmp-server community <removed>', configuration)
        ret = re.sub(r'snmp-server host ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}) version (\w{1,2}) .*',
                     r'snmp-server host \1 version \2 <removed>', ret)
        ret = re.sub(r'(snmp mib community-map)\s+\S+\s+(engineid \S+)',
                     r'\1 <removed> \2', ret)
        ret = re.sub(r'(snmp-server user\s+\S+\s+\S+\s+auth\s+(?:md5|sha))\s+\S+(\s+priv(?:\s+(?:des|3des|aes-\d+))?)\s+\S+(\s+localizedkey|\s+access\s+\S+)?',
                lambda m: (f"{m.group(1)} <removed>"
                + (f"{m.group(2)} <removed>" if m.group(2) else "")
                + (m.group(3) if m.group(3) else "")),ret)
        ret = re.sub(r'(snmp-server host\s+\S+\s+(?:trap|traps|informs)\s+version\s+(?:1|2c|3(?:\s+(?:auth|noauth|priv))?))\s+\S+(\s+.*)?',
                     r'\1 <removed>\2',ret)
        ret = re.sub(r'(netconf-yang\s+cisco-ia\s+snmp-community-string\s+)\S+',r'\1<removed>',ret)
        return ret

    def remove_tacacs(self, configuration: str) -> str:
        # Mask tacacs server key lines (block form)
        ret = re.sub(
            r'(?m)^(?:(?!ssh).)*\bkey\s+\d+\s+\S+',
            lambda m: re.sub(r'(\bkey\s+\d+)\s+\S+', r'\1 <removed>', m.group(0)),
            configuration
        )

        # Mask tacacs-server keys lines (single-line form)
        ret = re.sub(
            r'(tacacs-server\s+keys\s+\d+)\s+\S+',
            r'\1 <removed>',
            ret
        )

        # Mask tacacs password lines
        ret = re.sub(
            r'(\spassword\s[57]\s)\S+',
            r'\1<removed>',
            ret
        )

        ret = re.sub(r'((?:tacacs-server|radius-server)(?:\s+host\s+\S+)?\s+\S+\s+username\s+\S+\s+password\s+)\S+',
              r'\1<removed>',ret)

        ret = re.sub(r'(\slog trap\s)[^\s.]*', r'\1<removed>', ret)

        return ret

    def remove_app_hosting(self, configuration: str) -> str:
        ret = re.sub(r'(run-opts\s+\d+\s+["\']?\s*(?:--env|-e)\s+\w+=)\S+', r'\1<removed>', configuration)     
        return ret

    def apply(self, configuration: str, mask: int) -> str:
        """Apply all removers based on the mask bit flags."""
        for bit, func in self.removers.items():
            if mask & bit:
                configuration = func(configuration)
        return configuration

def startinteractivesession(name, host, user, password):
    try:
        print(f"Connecting to {name}...")
        # Check if sshpass is installed
        if shutil.which("sshpass"):
            # Use sshpass to provide password automatically
            subprocess.run([
                "sshpass", "-p", password,
                "ssh", f"{user}@{host}"
            ])
        else:
            # Fallback: run ssh normally (will prompt for password)
            print("sshpass not found, falling back to manual password entry...")
            subprocess.run(["ssh", f"{user}@{host}"])
    except Exception as e:
        print(f"Error starting SSH: {e}")


def load_commands(commandfile: str) -> dict[str, list[str]]:
    parser = configparser.ConfigParser(allow_no_value=True)
    parser.optionxform = str  # preserve case

    parser.read(commandfile)

    commands_by_os: dict[str, list[str]] = {}

    for section in parser.sections():
        # Each line in the section is treated as a key (command)
        commands = list(parser[section].keys())
        commands_by_os[section] = commands

    return commands_by_os

if __name__=="__main__":
    pass