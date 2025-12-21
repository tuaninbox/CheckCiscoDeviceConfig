from .session import DeviceSession
import sys, traceback
class DeviceInventoryCollector(DeviceSession):
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
            result = self._run_session(out_format="json")
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

            if result.get("success"):
                output = result["output"]
                print(result)

                # Genie JSON output is nested under command key
                if self.os.lower() in ["ios", "iosxe", "nxos"]:
                    if isinstance(output, dict):
                        try:
                            show_ver = output.get("show version", {})
                            version_info = show_ver.get("version", {})

                            host_info["version"] = version_info.get("version")
                            host_info["uptime"] = version_info.get("uptime")
                            host_info["serial"] = version_info.get("chassis_sn") or version_info.get("processor_board_id")
                            host_info["model"] = version_info.get("platform") or version_info.get("chassis")
                        except Exception as e:
                            print(f"Genie parse failed: {e}")
                            # fallback: try to parse text if Genie fails
                            raw_text = output.get("show version")
                            if isinstance(raw_text, str):
                                host_info["version"] = self._fallback_parse_version(raw_text)
                    elif isinstance(output, str):
                        host_info["version"] = self._fallback_parse_version(output)
                else:
                    # Non-Cisco fallback
                    if isinstance(output, dict):
                        raw_text = output.get(commands[0], "")
                        if isinstance(raw_text, str):
                            host_info["version"] = self._fallback_parse_version(raw_text)
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
            fail_msg = f"{e} at {tb.filename}:{tb.lineno} - {tb.line}" if self.debug else e
            if self.fail_logger:
                self.fail_logger.error(f"{self.hostname} - {self.host} - {fail_msg}")
            return self.result


    # --- fallback parser for non-Cisco ---
    def _fallback_parse_version(self, output: str) -> str:
        for line in output.splitlines():
            if "Version" in line or "Software" in line:
                return line.strip()
        return None
    
    def get_interfaces(self):
        try:
            """
            Gather interface information:
            - name
            - interface status (oper_status)
            - line protocol status
            - type (physical interface type)
            Uses _run_session for execution, Genie for parsing Cisco outputs.
            """
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
        
                # Cisco Genie structured output
                if self.os.lower() in ["ios", "iosxe", "nxos"]:
                    if isinstance(output, dict):
                        parsed = output.get(cmd, {})
                        try:
                            # Genie "show interface" returns dict keyed by interface name
                            for name, data in parsed.items():
                                # Only include physical interfaces (skip deleted/virtual if needed)
                                if not data.get("is_deleted", False):
                                    interfaces.append({
                                        "name": name,
                                        "status": data.get("oper_status"),       # up/down
                                        "line_protocol": data.get("line_protocol"),  # up/down
                                        "type": data.get("type"),                # e.g. Ethernet, Loopback, etc.
                                    })
                        except Exception as e:
                            if self.fail_logger:
                                self.fail_logger.error(f"{self.hostname} - Genie parse failed: {e}")
                            raw_text = output.get(cmd)
                            if isinstance(raw_text, str):
                                interfaces.extend(self._fallback_parse_interfaces(raw_text))
                    elif isinstance(output, str):
                        interfaces.extend(self._fallback_parse_interfaces(output))
                else:
                    # Non-Cisco fallback
                    raw_text = output.get(cmd)
                    if isinstance(raw_text, str):
                        interfaces.extend(self._fallback_parse_interfaces(raw_text))

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
        """
        Fallback parser for 'show interface' text output.
        Extracts: name, oper_status, line_protocol, type.
        """
        interfaces = []
        current_intf = None

        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue

            # Typical IOS/NXOS line: "Ethernet0/0 is up, line protocol is up"
            if "line protocol" in line:
                parts = line.split()
                name = parts[0]
                oper_status = "up" if "is up" in line and "administratively down" not in line else "down"
                line_protocol = "up" if "line protocol is up" in line else "down"

                current_intf = {
                    "name": name,
                    "status": oper_status,
                    "line_protocol": line_protocol,
                    "type": None,  # will fill from later line if available
                }
                interfaces.append(current_intf)

            # Type line example: "Hardware is AmdP2, address is aabb.cc00.0100"
            elif line.lower().startswith("hardware is") and current_intf:
                try:
                    hw_type = line.split("Hardware is")[1].split(",")[0].strip()
                    current_intf["type"] = hw_type
                except Exception:
                    pass

        return interfaces

    
    def get_modules(self):
        try:
            """
            Gather module information (slot, model, serial).
            Uses _run_session for execution, Genie for parsing Cisco outputs.
            """
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
                parsed = output.get(cmd, {})

                if self.os.lower() in ["ios", "iosxe", "nxos"]:
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
                            print(f"Genie parse failed: {e}")
                            raw_text = output.get(cmd)
                            if isinstance(raw_text, str):
                                modules.extend(self._fallback_parse_modules(raw_text))
                    elif isinstance(output, str):
                        modules.extend(self._fallback_parse_modules(output))
                else:
                    raw_text = output.get(cmd)
                    if isinstance(raw_text, str):
                        modules.extend(self._fallback_parse_modules(raw_text))

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
        """
        Gather complete device inventory by delegating to individual functions:
        - get_host_info()
        - get_interfaces()
        - get_modules()
        Returns a single structured dict snapshot.
        """
        try:
            inventory = {
                "host_info": self.get_host_info(),
                "interfaces": self.get_interfaces(),
                "modules": self.get_modules(),
            }
            return inventory

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

if __name__=="__main__":
    pass