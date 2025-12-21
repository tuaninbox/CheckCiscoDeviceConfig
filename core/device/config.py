from .session import DeviceSession
import traceback, sys
import configparser
from pathlib import Path
import os



class DeviceConfigCollector(DeviceSession):

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