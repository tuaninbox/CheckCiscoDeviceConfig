import os
import sys, re
import traceback
#from napalm import get_network_driver
from netmiko import ConnectHandler
import subprocess, shutil
import configparser
from core.utility.utility import format_msg
from core.utility.sanitizer import SecretSanitizer, ConfigSanitizer




import configparser
from pathlib import Path

class DeviceSession:
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

    def _run_session(self, removepassword: int = 0, out_format: str = "text", optional_args=None):
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

        with ConnectHandler(**conn_params) as conn:
            sanitizer = SecretSanitizer()
            commands = self.cmdlist if isinstance(self.cmdlist, list) else [self.cmdlist]

            # Decide output container
            output_lines = {} if out_format == "json" else []

            for cmd in commands:
                if out_format == "json":
                    # Use Genie parser for structured data
                    raw_output = conn.send_command(cmd, use_genie=True)
                    parsed_output = raw_output  # Genie already returns structured dict
                    sanitized_output = sanitizer.apply(parsed_output, removepassword)
                    output_lines[cmd] = sanitized_output
                else:
                    # Plain text mode
                    raw_output = conn.send_command(cmd)
                    if self.sanitizeconfig:
                        clean_config = ConfigSanitizer.sanitize(raw_output, self.os, cmd)
                    else:
                        clean_config = raw_output
                    sanitized_output = sanitizer.apply(clean_config, removepassword)
                    output_lines.append(f"{self.hostname}# {cmd}\n{sanitized_output}")

            self.result["success"] = True
            # print(output_lines)
            # self.result["output"] = "\n".join(output_lines)
            self.result["output"] = output_lines

            if self.success_logger:
                self.success_logger.info(
                    f"{self.hostname} - {self.host} - Configuration retrieved successfully"
                )

        return self.result

if __name__=="__main__":
    pass