import os
import sys
import traceback
from napalm import get_network_driver
from core.utility import remove_password, format_msg

class DeviceDataRetriever:
    def __init__(self, hostname, host, user, password, cmdlist, success_logger=None, fail_logger=None, debug=0, outfolder="output"):
        self.hostname = hostname
        self.host = host
        self.user = user
        self.password = password
        self.cmdlist = cmdlist
        self.success_logger = success_logger
        self.fail_logger = fail_logger
        self.debug = debug
        self.outfolder = outfolder
        self.result = {
            "hostname": hostname,
            "host": host,
            "success": False,
            "output": "",
            "error": None
        }

    def _run_session(self, optional_args=None):
        driver = get_network_driver('ios')
        device = driver(self.host, self.user, self.password, optional_args=optional_args or {})
        device.open()

        commands = self.cmdlist if isinstance(self.cmdlist, list) else [self.cmdlist]
        output_lines = []
        for cmd in commands:
            r = device.cli([cmd])
            output_lines.append(f"{self.hostname}# {cmd}\n{remove_password(r[cmd])}")

        device.close()
        self.result["success"] = True
        self.result["output"] = "\n".join(output_lines)
        if self.success_logger:
            self.success_logger.info(f"{self.hostname} - {self.host} → Configuration retrieved successfully")
        return self.result

    def get_config(self):
        try:
            return self._run_session()
        except:
            try:
                return self._run_session(optional_args={"transport": "telnet"})
            except Exception as e:
                tb = traceback.extract_tb(sys.exc_info()[2])[0]
                self.result["success"]= False
                self.result["error"] = {
                    "message": str(e),
                    "filename": tb.filename,
                    "line": tb.lineno,
                    "code": tb.line
                }
                fail_msg = f"{e} at {tb.filename}:{tb.lineno} → {tb.line}" if self.debug else e
                if self.fail_logger:
                    self.fail_logger.error(f"{self.hostname} - {self.host} → {fail_msg}")
                return self.result

    def get_config_to_file(self):
        try:
            output = self.get_config()
            # print(type(output["success"]),output["success"])
            if output["success"]:
                outfolder = self.outfolder
                outfile = os.path.join(outfolder, f"{self.hostname}.txt")
                if not os.path.exists(outfolder):
                    os.makedirs(outfolder)
                with open(outfile, "w") as fp:
                    fp.write(output["output"])
                return format_msg(f"Configuration of {self.hostname} - {self.host} saved in {outfile}","BLUE")
            else:
                # result["message"]=f"Can't get command output from devices {self.hostname} - {self.host}"
                fail_msg= f"{output['error']['message']} at {output['error']['filename']}: {output['error']['line']} → {output['error']['code']}" if self.debug else f"{output['error']['message']}"
                return format_msg(f"{self.hostname} - {self.host} → {fail_msg}","RED")
                # return format_msg(f"Can't get command output from devices {self.hostname} - {self.host}","RED")
        except:
            # result["message"]=f"Write configuration to file error {sys.exc_info()[1]} for site {self.hostname} - {self.host}"
            return format_msg(f"Write configuration to file error {sys.exc_info()[1]} for site {self.hostname} - {self.host}","RED")
        
