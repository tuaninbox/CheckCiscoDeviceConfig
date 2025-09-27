import os, getpass

def get_credentials():
    username = os.environ.get("username")
    password = os.environ.get("password")

    if not username:
        username = input("Enter username: ")
    if not password:
        password = getpass.getpass("Enter password: ")

    # Ask user if they want to save credentials
    # save = input("Do you want to save these credentials for future use? (y/n): ").strip().lower()
    # if save == 'y':
    #     os.environ["acc"] = username
    #     os.environ["cred"] = password
    #     print("Credentials saved in environment for this session.")
    return username, password