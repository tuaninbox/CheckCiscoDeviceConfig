from netmiko import ConnectHandler
from datetime import datetime
import os, sys
from pathlib import Path

OS_MAPPING = {
    "ios": "cisco_ios",
    "iosxe": "cisco_xe",
    "nxos": "cisco_nxos",
}
    
class DeviceConfigurator:
    def __init__(self, device_row, username, password, commands, verification, success_logger, fail_logger):
        self.device_row = device_row
        self.username = username
        self.password = password
        self.commands = commands
        self.verification = verification
        self.success_logger = success_logger
        self.fail_logger = fail_logger

        self.host = device_row["Host"]
        self.address = device_row["IP"]
        # map OS to Netmiko device_type
        raw_type = device_row.get("OS", "").lower()
        self.device_type = OS_MAPPING.get(raw_type, raw_type)

        self.port = int(device_row.get("Port") or 22)

    # def _connect(self):
    #     return ConnectHandler(
    #         device_type=self.device_type,
    #         host=self.address,
    #         port=self.port,
    #         username=self.username,
    #         password=self.password,
    #     )

    def _connect(self, session_log=False, fast_cli=False):
        """
        Create and return a Netmiko connection.

        Parameters
        ----------
        session_log : bool | str | pathlib.Path | IO | None
            - False or None (default): disable Netmiko session logging
            - True: enable and write to ./logs/<host>_<timestamp>.log
            - str / Path: file path to write the transcript
            - file-like (e.g., sys.stdout): stream to write the transcript
        fast_cli : bool
            Forwarded to Netmiko (False is safer for slower devices)
        
        Usage
        ----------
        # 1) No logging (default)
        conn = self._connect()

        # 2) Enable logging with a default timestamped file under ./logs
        conn = self._connect(session_log=True)

        # 3) Log to a specific file (path is created if needed)
        conn = self._connect(session_log="./logs/edge01_run.log")

        # 4) Log to console (stdout) while debugging
        import sys
        conn = self._connect(session_log=sys.stdout)

        # 5) Append instead of overwrite (optional): change file mode in _connect()
        # session_log_file_mode="append"
        """

        # Decide what to pass to Netmiko's 'session_log' parameter
        nm_session_log = None
        if session_log is True:
            # Use a default file under ./logs when caller just says "True"
            log_dir = Path("./logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            nm_session_log = str(log_dir / f"{self.host}_{stamp}.log")
        elif session_log in (False, None):
            nm_session_log = None
        else:
            # Caller provided explicit path or stream
            if hasattr(session_log, "write"):
                # It's a file-like object (e.g., sys.stdout)
                nm_session_log = session_log
            else:
                # Treat as a path
                p = Path(session_log)
                p.parent.mkdir(parents=True, exist_ok=True)
                nm_session_log = str(p)

        conn = ConnectHandler(
            device_type=self.device_type,
            host=self.address,
            username=self.username,
            password=self.password,
            secret=getattr(self, "enable_secret", None),
            port=self.port,
            fast_cli=fast_cli,
            session_log=nm_session_log,            # <-- on/off per call
            session_log_record_writes=True,        # include commands you send
            session_log_file_mode="write",         # change to "append" if desired
        )

        # Enter enable if secret provided
        if getattr(self, "enable_secret", None):
            conn.enable()

        # Disable paging; ignore platform differences
        try:
            conn.send_command_timing("terminal length 0")
        except Exception:
            pass

        # Optional: emit where we�re logging (for your Python logger)
        try:
            if nm_session_log is None:
                self.success_logger.info(f"[{self.host}] Netmiko session log: disabled")
            elif nm_session_log is sys.stdout:
                self.success_logger.info(f"[{self.host}] Netmiko session log: console (stdout)")
            elif isinstance(nm_session_log, str):
                self.success_logger.info(f"[{self.host}] Netmiko session log ? {os.path.abspath(nm_session_log)}")
        except Exception:
            pass


    
    def _save_config_cross_platform(self, conn):
        """
        Save running-config to startup-config across IOS/IOS-XE and NX-OS.
        Returns (save_ok: bool, save_msg: str)
        """
        import time
        import re

        # 1) Make sure we are in exec (not config) and have enable
        try:
            if conn.check_config_mode():
                conn.exit_config_mode()
        except Exception as ex_ecm:
            # Try again once; don't hard-fail saving just because of a noisy exit
            try:
                conn.exit_config_mode()
            except Exception:
                self.fail_logger.warning(f"[{self.host}] exit_config_mode warning: {ex_ecm}")

        if not conn.check_enable_mode():
            conn.enable()

        device_type = getattr(conn, "device_type", "").lower()
        save_msg = ""
        save_ok = False

        try:
            # 2) IOS/IOS-XE path (cisco_ios, cisco_xe)
            if "cisco_ios" in device_type or "cisco_xe" in device_type:
                # Prefer Netmiko helper if present (issues 'write memory' for IOS/IOS-XE)
                if hasattr(conn, "save_config"):
                    save_msg = conn.save_config()
                    save_ok = True
                else:
                    # 'write memory' is simple and usually prompt-free on IOS/IOS-XE
                    save_msg = conn.send_command_timing(
                        "write memory", strip_prompt=False, strip_command=False
                    )
                    # Heuristic: many devices echo [OK] or OK, but not all. Verify prompt returns.
                    if "[OK]" in save_msg or "OK" in save_msg:
                        save_ok = True
                    else:
                        # Give the device a moment then ensure we have a prompt
                        time.sleep(0.3)
                        _ = conn.find_prompt()
                        save_ok = True

            # 3) NX-OS path (cisco_nxos)
            elif "cisco_nxos" in device_type:
                # Optional: suppress q/a for the life of the session
                # (ignore failure if feature not supported on your NX-OS train)
                try:
                    conn.send_command_timing("terminal dont-ask")
                except Exception:
                    pass

                # Use timing mode; be ready to press Enter on destination prompt
                out = conn.send_command_timing(
                    "copy running-config startup-config",
                    strip_prompt=False, strip_command=False
                )
                if "Destination filename" in out or "]?" in out:
                    out += conn.send_command_timing("\n")  # accept default
                # Some images print "Copy complete." or "Copy complete"
                save_msg = out
                if "Copy complete" in out or "copied" in out.lower():
                    save_ok = True
                else:
                    # If we didn't catch the success string, at least ensure we have a prompt back
                    time.sleep(0.3)
                    _ = conn.find_prompt()
                    save_ok = True

            # 4) Fallback for any other platform: try 'copy run start' with timing
            else:
                out = conn.send_command_timing(
                    "copy running-config startup-config",
                    strip_prompt=False, strip_command=False
                )
                if "Destination filename" in out or "]?" in out:
                    out += conn.send_command_timing("\n")
                save_msg = out
                # Confirm prompt returns
                time.sleep(0.3)
                _ = conn.find_prompt()
                save_ok = True

            return save_ok, save_msg

        except Exception as se:
            return False, f"{se}"

    def apply_config(self):
        result = {
            "device": self.host,
            "address": self.address,
            "status": "",
            "details": ""
        }

        conn = None
        try:
            # 1) Connect
            conn = self._connect() #session_log=f"netmiko_{self.host}.log")
            self.success_logger.info(f"[{self.host}] Connected on port {self.port}")

            # 2) Push config set
            cfg_output = conn.send_config_set(self.commands)
            self.success_logger.info(f"[{self.host}] Config applied:\n{cfg_output}")

            # 3) Verify
            verify_cmd = self.verification.get("check")
            expected = self.verification.get("expect")
            if not verify_cmd or expected is None:
                raise ValueError(
                    f"Verification block incomplete. Got check={verify_cmd!r}, expect={expected!r}"
                )

            verify_output = conn.send_command(verify_cmd)
            self.success_logger.info(f"[{self.host}] Verification output:\n{verify_output}")

            # 4) Decide success/failure
            if expected in verify_output:
                result["status"] = "success"
                result["details"] = f"Verified: '{expected}' found"
                self.success_logger.info(f"[{self.host}] SUCCESS: '{expected}' found")

                save_ok, save_msg = self._save_config_cross_platform(conn)
                if save_ok:
                    self.success_logger.info(f"[{self.host}] Save configuration output:\n{save_msg}")
                    result["details"] += " | Config saved to startup-config"
                else:
                    self.fail_logger.error(f"[{self.host}] ERROR saving configuration: {save_msg}")
                    result["details"] += f" | SAVE FAILED: {save_msg}"

            else:
                # Verification failed; do not save
                result["status"] = "failed"
                result["details"] = f"Expected '{expected}' not found"
                self.fail_logger.error(f"[{self.host}] FAILED: '{expected}' not found")

        except Exception as e:
            result["status"] = "failed"
            result["details"] = str(e)
            self.fail_logger.error(f"[{self.host}] ERROR: {str(e)}")

        finally:
            # Always disconnect cleanly
            try:
                if conn:
                    conn.disconnect()
                    self.success_logger.info(f"[{self.host}] Disconnected")
            except Exception as de:
                self.fail_logger.warning(f"[{self.host}] Disconnect warning: {de}")

        return result

