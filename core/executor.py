import concurrent.futures
from .device import DeviceDataRetriever
from .device_configurator import DeviceConfigurator

import concurrent.futures
from .device import DeviceDataRetriever


def get_device_config(yaml_dict, vendor, os_type, device_type):
    """
    Extract the config block for a specific vendor/os/device_type
    from a pre-loaded YAML dictionary.
    """

    try:
        return yaml_dict["vendors"][vendor][os_type][device_type]
    except KeyError:
        raise ValueError(
            f"No configuration found for vendor={vendor}, os={os_type}, device={device_type}"
        )
    
def run_parallel(reader, yaml_cmds, username, password, run_func,
                 filterlist=None, sanitizeconfig=True,
                 removepassword=1|2|4|8, **extra_kwargs):

    rows = list(reader)
    results = []

    mode = extra_kwargs.get("mode", "retrieve")
    success_logger = extra_kwargs.get("success_logger")
    fail_logger = extra_kwargs.get("fail_logger")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []

        for row in rows:
            if row["Host"].startswith("#"):
                continue
            if filterlist and row["Host"].lower() not in filterlist:
                continue

            vendor = row.get("Vendor", "").strip().lower()
            os_type = row.get("OS", "").strip().lower()
            device_type = row.get("Type", "").strip().lower()

            if mode == "configure":
                try:
                    config_block = get_device_config(
                        yaml_cmds, vendor, os_type, device_type
                    )
                except Exception as e:
                    fail_logger.error(f"[{row['Host']}] YAML lookup failed: {e}")
                    results.append({
                        "device": row["Host"],
                        "status": "failed",
                        "details": str(e)
                    })
                    continue

                commands = config_block.get("commands", [])
                verification = config_block.get("verification", {})

                obj = DeviceConfigurator(
                    device_row=row,
                    username=username,
                    password=password,
                    commands=commands,
                    verification=verification,
                    success_logger=success_logger,
                    fail_logger=fail_logger
                )

            else:
                # Retrieval mode ? use cmd list directly
                device_cmds = yaml_cmds  # or whatever your retrieval commands are
                obj = DeviceDataRetriever(
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

            futures.append(executor.submit(run_func, obj))

        for future in futures:
            results.append(future.result())

    return results


# import concurrent.futures
# from core.device.config import DeviceConfigCollector
# from core.device.inventory import DeviceInventoryCollector

# def run_parallel(
#     reader,
#     cmd,
#     username,
#     password,
#     collector_type: str = "inventory",   # "inventory" or "config"
#     config_mode: str = "return",         # "return" or "file"
#     filterlist=None,
#     sanitizeconfig=True,
#     removepassword: int = 15,
#     **extra_kwargs
# ):
#     rows = list(reader)
#     results = []

#     if collector_type == "inventory":
#         CollectorClass = DeviceInventoryCollector
#         run_method = "get_inventory"
#     elif collector_type == "config":
#         CollectorClass = DeviceConfigCollector
#         run_method = "get_config_to_file" if config_mode == "file" else "get_config"
#     else:
#         raise ValueError(f"Unsupported collector_type: {collector_type}")

#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         futures = []
#         for row in rows:
#             if row["Host"].startswith("#"):
#                 continue
#             if filterlist and row["Host"].lower() not in filterlist:
#                 continue

#             os_type = row.get("OS", "").strip().lower()
#             device_cmds = cmd.get(os_type, []) if isinstance(cmd, dict) else cmd

#             retriever = CollectorClass(
#                 hostname=row["Host"],
#                 host=row["IP"],
#                 os=row["OS"],
#                 user=username,
#                 password=password,
#                 cmdlist=device_cmds,
#                 sanitizeconfig=sanitizeconfig,
#                 removepassword=removepassword,
#                 **extra_kwargs
#             )

#             futures.append(executor.submit(getattr(retriever, run_method)))

#         for future in futures:
#             results.append(future.result())

#     return results
