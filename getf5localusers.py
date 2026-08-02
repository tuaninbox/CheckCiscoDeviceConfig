import csv
from netmiko import ConnectHandler

CSV_FILE = "devices.csv"

def load_devices(csv_file):
    devices = []
    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize OS field
            os_type = (row.get("OS") or "").strip().lower()

            # Only include F5 devices
            if os_type in ["f5", "f5_tmsh", "bigip"]:
                devices.append({
                    "host": row["IP"],
                    "hostname": row["Host"],
                    "port": int(row["Port"]) if row["Port"] else 22,
                    "device_type": "f5_tmsh",
                    "username": "admin",          # adjust as needed
                    "password": "yourpassword"    # adjust as needed
                })
    return devices


def get_local_users(conn):
    output = conn.send_command("tmsh list auth user")
    users = []

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("auth user"):
            # Example: auth user admin {
            parts = line.split()
            if len(parts) >= 3:
                users.append(parts[2])
    return users


def main():
    devices = load_devices(CSV_FILE)

    for dev in devices:
        host = dev["host"]
        name = dev["hostname"]

        print(f"Connecting to {name} ({host})...")

        try:
            conn = ConnectHandler(
                device_type=dev["device_type"],
                host=dev["host"],
                port=dev["port"],
                username=dev["username"],
                password=dev["password"]
            )

            users = get_local_users(conn)
            conn.disconnect()

            user_list = ", ".join(users) if users else "No users found"
            print(f"{name}: {user_list}")

        except Exception as e:
            print(f"{name}: ERROR - {e}")


if __name__ == "__main__":
    main()
