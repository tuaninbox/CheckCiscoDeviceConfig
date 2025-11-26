import os, getpass, configparser

def get_credentials(filename="~/.backupcred"):
    username = None
    password = None

    # Expand ~ to full path
    filename = os.path.expanduser(filename)

    # 1. Try reading from credential file using configparser
    if os.path.exists(filename):
        config = configparser.ConfigParser()
        config.read(filename)

        if "credentials" in config:
            username = config["credentials"].get("username")
            password = config["credentials"].get("password")

    # 2. Fall back to environment variables
    if not username:
        username = os.environ.get("username")
    if not password:
        password = os.environ.get("password")

    # 3. Prompt user if still missing
    if not username:
        username = input("Enter username: ")
    if not password:
        password = getpass.getpass("Enter password: ")

    return username, password

if __name__=="__main__":
    print(get_credentials())