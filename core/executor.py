
import concurrent.futures
from .device import DeviceDataRetriever

def run_parallel(reader, cmd, username, password, run_func, filterlist=None, **extra_kwargs):
    rows = list(reader)  # materialize reader so we can iterate multiple times
    results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for row in rows:
            if row["Host"].startswith("#"):
                continue
            if filterlist and row["Host"] not in filterlist:
                continue

            os_type = row.get("OS", "").strip().lower()
            device_cmds = cmd.get(os_type, []) if isinstance(cmd, dict) else cmd

            futures.append(
                executor.submit(
                    run_func,
                    DeviceDataRetriever(
                        hostname=row["Host"],
                        host=row["IP"],
                        os=row["OS"],
                        user=username,
                        password=password,
                        cmdlist=device_cmds,
                        **extra_kwargs
                    )
                )
            )

        for future in futures:
            results.append(future.result())

    return results


# import concurrent.futures
# from .device import DeviceDataRetriever  # Adjust import path as needed

# def run_parallel(reader, cmd, username, password, run_func, filterlist=None, **extra_kwargs):
#     results = []
#     for row in reader:
#         os_type = row.get("OS", "").strip().lower()
#         if isinstance(cmd, dict):
#             # Pick commands for this device’s OS
#             device_cmds = cmd.get(os_type, [])
#         else:
#             # cmd is already a list (from -c)
#             device_cmds = cmd
#     # print(device_cmds)
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         if filterlist:
#             futures = [
#                 executor.submit(
#                     run_func,
#                     DeviceDataRetriever(
#                         hostname=i["Host"],
#                         host=i["IP"],
#                         user=username,
#                         password=password,
#                         # user=username if not i["Username"] else i["Username"],
#                         # password=password if not i["Password"] else i["Password"],
#                         cmdlist=device_cmds,
#                         **extra_kwargs
#                     )
#                 )
#                 for i in reader if not i["Host"].startswith("#") and i["Host"] in filterlist
#             ]
#         else:
#             futures = [
#                 executor.submit(
#                     run_func,
#                     DeviceDataRetriever(
#                         hostname=i["Host"],
#                         host=i["IP"],
#                         user=username,
#                         password=password,
#                         # user=username if not i["Username"] else i["Username"],
#                         # password=password if not i["Password"] else i["Password"],
#                         cmdlist=device_cmds,
#                         **extra_kwargs
#                     )
#                 )
#                 for i in reader if not i["Host"].startswith("#")
#             ]
#         for future in futures:
#             results.append(future.result())
#     return results
