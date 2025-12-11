import os
import sys, re
import traceback
#from napalm import get_network_driver
from netmiko import ConnectHandler
import subprocess, shutil
import configparser
from core.utility import format_msg
from genie.libs.parser.utils import get_parser


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


class DeviceDataRetriever:
    def __init__(self, hostname, host, os, user, password, cmdlist, success_logger=None, fail_logger=None, debug=0, outfolder="output", sanitizeconfig=True, removepassword: int = 1|2|4|8):
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
        self.removepassword = removepassword
        self.result = {
            "hostname": hostname,
            "host": host,
            "success": False,
            "output": "",
            "error": None
        }

    def _run_session(self, removepassword: int = 0, use_parser_genie=False, optional_args=None):
        # Map OS string to Netmiko device_type
        device_type_map = {
            "ios": "cisco_ios",
            "iosxe": "cisco_iosxe",
            "nxos": "cisco_nxos",
            "aironet": "cisco_wlc",
            "dellos10": "dell_os10",
            "f5": "f5_tmsh",  # or "f5_ltm" depending on CLI
        }
        device_type = device_type_map.get(self.os)
        if not device_type:
            self.result["error"] = f"Unsupported OS type: {self.os}"
            if self.fail_logger:
                self.fail_logger.error(self.result["error"])
            return self.result

        conn_params = {
            "device_type": device_type,
            "ip": self.host,
            "username": self.user,
            "password": self.password,
        }
        if optional_args:
            conn_params.update(optional_args)

        # try:
        with ConnectHandler(**conn_params) as conn:
            sanitizer = SecretSanitizer()

            commands = self.cmdlist if isinstance(self.cmdlist, list) else [self.cmdlist]
            output_lines = []

            for cmd in commands:
                if use_parser_genie:
                    raw_output = conn.send_command(cmd, use_genie=True)
                else:
                    raw_output = conn.send_command(cmd)
                if self.sanitizeconfig:
                    clean_config = sanitize_config(raw_output, self.os, cmd)
                else:
                    clean_config = raw_output
                sanitized_output = sanitizer.apply(clean_config, removepassword)
                print(sanitized_output)
                if use_parser_genie:
                    output_lines[f"{cmd}"]=sanitized_output
                    # print(output_lines)
                else:
                    output_lines.append(f"{self.hostname}# {cmd}\n{sanitized_output}")

            self.result["success"] = True
            self.result["output"] = output_lines

            if self.success_logger:
                self.success_logger.info(
                    f"{self.hostname} - {self.host} - Configuration retrieved successfully"
                )

        return self.result

    def get_config(self):
        try:
            return self._run_session(self.removepassword)
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
        
    def get_host_info(self):
        try:
            """
            Gather host information (version, uptime, serial, model).
            Uses _run_session for execution, Genie for parsing Cisco outputs.
            """
            os_cmds = {
                "ios": ["show version"],
                "iosxe": ["show version"],
                "nxos": ["show version"],
                "aironet": ["show sysinfo"],
                "dellos10": ["show version"],
                "f5": ["show sys version"],
            }

            commands = os_cmds.get(self.os.lower())
            if not commands:
                raise ValueError(f"Unsupported OS type: {self.os}")

            # Save current cmdlist and override
            original_cmdlist = self.cmdlist
            self.cmdlist = commands

            # Run session (reuses connection + sanitization)
            result = self._run_session(use_parser_genie=True)
            # Restore original cmdlist
            self.cmdlist = original_cmdlist

            host_info = {
                "hostname": self.hostname,
                "ip": self.host,
                "os": self.os,
                "version": None,
                "uptime": None,
                "serial": None,
                "model": None,
            }

            if result["success"]:
                output = result["output"]
                print(output)
                # Use Genie for Cisco platforms
                if self.os.lower() in ["ios", "iosxe", "nxos"]:
                    try:
                        # parser = get_parser("show version", self.os.lower())
                        # parsed = parser(output)
                        parser_cls = get_parser("show version", self.os.lower())
                        parser = parser_cls(device=None)
                        parsed = parser.parse(output)
                        print(parsed)
                        host_info["version"] = parsed.get("version")
                        host_info["uptime"] = parsed.get("uptime")
                        host_info["serial"] = parsed.get("processor_board_id")
                        host_info["model"] = parsed.get("chassis")
                    except Exception as e:
                        # fallback if Genie parser fails
                        print(f"Genie parsed failed {e}")
                        host_info["version"] = self._fallback_parse_version(output)
                else:
                    # Non-Cisco fallback
                    host_info["version"] = self._fallback_parse_version(output)
                result['output']=host_info
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
        return host_info

    # --- fallback parser for non-Cisco ---
    def _fallback_parse_version(self, output: str) -> str:
        for line in output.splitlines():
            if "Version" in line or "Software" in line:
                return line.strip()
        return None
    
class SecretSanitizer:
    def __init__(self):
        # Map bitmask values to methods
        self.removers = {
            1: self.remove_userpass,
            2: self.remove_snmp,
            4: self.remove_key,
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
        ret = re.sub(r'(snmp-server\s+host\s+\S+(?:\s+vrf\s+\S+)?(?:\s+(?:trap|traps|informs))?(?:\s+version\s+(?:1|2c|3(?:\s+(?:auth|noauth|priv))?))?)(?:\s+(?!use-vrf)\S+)',r'\1 <removed>',ret)
        ret = re.sub(r'(netconf-yang\s+cisco-ia\s+snmp-community-string\s+)\S+',r'\1<removed>',ret)
        ret = re.sub(
            r'(snmp community (?:create|accessmode ro)|snmp trapreceiver (?:mode enable|create))'
            r'\s+(\S+)(?:\s+([0-9]{1,3}(?:\.[0-9]{1,3}){3}))?',
            lambda m: (
                f"{m.group(1)} <removed>"
                + (f" {m.group(3)}" if m.group(3) else "")
            ),
            ret
        )
        return ret

    def remove_key(self, configuration: str) -> str:
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

        # Remove Tacacs or radius server key
        ret = re.sub(r'((?:tacacs-server|radius-server)(?:\s+host\s+\S+)?\s+\S+\s+username\s+\S+\s+password\s+)\S+',
              r'\1<removed>',ret)

        # Remove Log Trap
        ret = re.sub(r'(\slog trap\s)[^\s.]*', r'\1<removed>', ret)

        # Mask OSPF message-digest-key secrets
        ret = re.sub(
                    r'(ip\s+ospf\s+message-digest-key\s+\d+\s+\S+\s+\d+)\s+\S+',
                    r'\1 <removed>',
                    ret
        )

        # Mask client/server-key secrets
        ret = re.sub(
                    r'(server-key\s+\d+)\s+\S+',
                    r'\1 <removed>',
                    ret
        )
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