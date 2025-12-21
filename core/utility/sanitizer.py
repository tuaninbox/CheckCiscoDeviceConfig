import os, re
import configparser
class ConfigSanitizer:
    @staticmethod
    def sanitize(raw_output: str, os_name: str, command: str, config_file: str = "config/commandfilters.ini") -> str:
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
        ret = re.sub(r'(mgmtuser\s+username\s+\S+\s+password\s+\d+)\s+\S+\s+(secret\s+\d+)\s+\S+',r'\1 <removed> \2 <removed>',ret)
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