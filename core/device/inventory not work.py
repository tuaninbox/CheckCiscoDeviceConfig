from .session import DeviceSession
import sys, traceback

class DeviceInventoryCollector(DeviceSession):

    def get_host_info(self):
        try:
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

            original_cmdlist = self.cmdlist
            self.cmdlist = commands
            result = self._run_session(out_format="json")
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

            if result.get("success"):
                output = result["output"]
                cmd = commands[0]

                if isinstance(output, dict):
                    show_ver = output.get(cmd, {})
                    version_info = show_ver.get("version", {})
                    host_info["version"] = version_info.get("version")
                    host_info["uptime"] = version_info.get("uptime")
                    host_info["serial"] = version_info.get("chassis_sn") or version_info.get("processor_board_id")
                    host_info["model"] = version_info.get("platform") or version_info.get("chassis")
                elif isinstance(output, str):
                    host_info["version"] = self._fallback_parse_version(output)

            return host_info

        except Exception as e:
            tb = traceback.extract_tb(sys.exc_info()[2])[0]
            self.result["success"] = False
            self.result["error"] = {
                "message": str(e),
                "filename": tb.filename,
                "line": tb.lineno,
                "code": tb.line
            }
            if self.fail_logger:
                self.fail_logger.error(f"{self.hostname} - {self.host} - {e}")
            return self.result

    def _fallback_parse_version(self, output: str) -> str:
        for line in output.splitlines():
            if "Version" in line or "Software" in line:
                return line.strip()
        return None

    def get_interfaces(self):
        try:
            os_cmds = {
                "ios": ["show interface"],
                "iosxe": ["show interface"],
                "nxos": ["show interface"],
                "aironet": ["show interface summary"],
                "dellos10": ["show interface"],
                "f5": ["tmsh show net interface"],
            }
            commands = os_cmds.get(self.os.lower())
            if not commands:
                raise ValueError(f"Unsupported OS type: {self.os}")

            original_cmdlist = self.cmdlist
            self.cmdlist = commands
            result = self._run_session(out_format="json")
            self.cmdlist = original_cmdlist

            interfaces = []
            if result.get("success"):
                output = result["output"]
                cmd = commands[0]

                if isinstance(output, dict):
                    parsed = output.get(cmd, {})
                    try:
                        for name, data in parsed.items():
                            if not data.get("is_deleted", False):
                                interfaces.append({
                                    "name": name,
                                    "status": data.get("oper_status"),
                                    "line_protocol": data.get("line_protocol"),
                                    "type": data.get("type"),
                                })
                    except Exception as e:
                        if self.fail_logger:
                            self.fail_logger.error(f"{self.hostname} - Genie parse failed: {e}")
                        raw_text = output.get(cmd) if isinstance(output, dict) else output
                        if isinstance(raw_text, str):
                            interfaces.extend(self._fallback_parse_interfaces(raw_text))
                elif isinstance(output, str):
                    interfaces.extend(self._fallback_parse_interfaces(output))

            return interfaces

        except Exception as e:
            tb = traceback.extract_tb(sys.exc_info()[2])[0]
            self.result["success"] = False
            self.result["error"] = {
                "message": str(e),
                "filename": tb.filename,
                "line": tb.lineno,
                "code": tb.line
            }
            return self.result

    def _fallback_parse_interfaces(self, output: str):
        interfaces = []
        current_intf = None
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            if "line protocol" in line:
                parts = line.split()
                name = parts[0]
                oper_status = "up" if "is up" in line and "administratively down" not in line else "down"
                line_protocol = "up" if "line protocol is up" in line else "down"
                current_intf = {
                    "name": name,
                    "status": oper_status,
                    "line_protocol": line_protocol,
                    "type": None,
                }
                interfaces.append(current_intf)
            elif line.lower().startswith("hardware is") and current_intf:
                try:
                    hw_type = line.split("Hardware is")[1].split(",")[0].strip()
                    current_intf["type"] = hw_type
                except Exception:
                    pass
        return interfaces

    def get_modules(self):
        try:
            os_cmds = {
                "ios": ["show module"],
                "iosxe": ["show module"],
                "nxos": ["show module"],
                "aironet": ["show inventory"],
                "dellos10": ["show inventory"],
                "f5": ["show sys hardware"],
            }
            commands = os_cmds.get(self.os.lower())
            if not commands:
                raise ValueError(f"Unsupported OS type: {self.os}")

            original_cmdlist = self.cmdlist
            self.cmdlist = commands
            result = self._run_session(out_format="json")
            self.cmdlist = original_cmdlist

            modules = []
            if result.get("success"):
                output = result["output"]
                cmd = commands[0]

                if isinstance(output, dict):
                    parsed = output.get(cmd, {})
                    try:
                        mod_info = parsed.get("slot", {})
                        for slot, data in mod_info.items():
                            modules.append({
                                "slot": slot,
                                "model": data.get("model"),
                                "serial": data.get("serial_number"),
                                "status": data.get("status"),
                            })
                    except Exception as e:
                        if self.fail_logger:
                            self.fail_logger.error(f"{self.hostname} - Genie parse failed: {e}")
                        raw_text = output.get(cmd) if isinstance(output, dict) else output
                        if isinstance(raw_text, str):
                            modules.extend(self._fallback_parse_modules(raw_text))
                elif isinstance(output, str):
                    modules.extend(self._fallback_parse_modules(output))

            return modules

        except Exception as e:
            tb = traceback.extract_tb(sys.exc_info()[2])[0]
            self.result["success"] = False
            self.result["error"] = {
                "message": str(e),
                "filename": tb.filename,
                "line": tb.lineno,
                "code": tb.line
            }
            return self.result

    def _fallback_parse_modules(self, output: str):
        modules = []
        for line in output.splitlines():
            if line and not line.startswith("Slot"):
                parts = line.split()
                if len(parts) >= 3:
                    modules.append({
                        "slot": parts[0],
                        "model": parts[1],
                        "serial": parts[2],
                    })
        return modules

    def get_inventory(self):
        try:
            return {
                "host_info": self.get_host_info(),
                "interfaces": self.get_interfaces(),
                "modules": self.get_modules(),
            }
        except Exception as e:
            tb = traceback.extract_tb(sys.exc_info()[2])[0]
            self.result["success"] = False
            self.result["error"] = {
                "message": str(e),
                "filename": tb.filename,
                "line": tb.lineno,
                "code": tb.line
            }
            return self.result

if __name__ == "__main__":
    pass
