import concurrent.futures
from core.device.config import DeviceConfigCollector
from core.device.inventory import DeviceInventoryCollector

def run_parallel(
    reader,
    cmd,
    username,
    password,
    collector_type: str = "inventory",   # "inventory" or "config"
    config_mode: str = "return",         # "return" or "file"
    filterlist=None,
    sanitizeconfig=True,
    removepassword: int = 15,
    **extra_kwargs
):
    rows = list(reader)
    results = []

    if collector_type == "inventory":
        CollectorClass = DeviceInventoryCollector
        run_method = "get_inventory"
    elif collector_type == "config":
        CollectorClass = DeviceConfigCollector
        run_method = "get_config_to_file" if config_mode == "file" else "get_config"
    else:
        raise ValueError(f"Unsupported collector_type: {collector_type}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for row in rows:
            if row["Host"].startswith("#"):
                continue
            if filterlist and row["Host"].lower() not in filterlist:
                continue

            os_type = row.get("OS", "").strip().lower()
            device_cmds = cmd.get(os_type, []) if isinstance(cmd, dict) else cmd

            retriever = CollectorClass(
                hostname=row["Host"],
                host=row["IP"],
                os=row["OS"],
                user=username,
                password=password,
                cmdlist=device_cmds,
                sanitizeconfig=sanitizeconfig,
                removepassword=removepassword,
                **extra_kwargs
            )

            futures.append(executor.submit(getattr(retriever, run_method)))

        for future in futures:
            results.append(future.result())

    return results
