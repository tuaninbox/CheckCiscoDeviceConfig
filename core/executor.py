import concurrent.futures
from .device import DeviceDataRetriever  # Adjust import path as needed

def run_parallel(reader, cmd, username, password, run_func, **extra_kwargs):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                run_func,
                DeviceDataRetriever(
                    hostname=i["Name"],
                    host=i["Host"],
                    user=username if not i["Username"] else i["Username"],
                    password=password if not i["Password"] else i["Password"],
                    cmdlist=cmd,
                    **extra_kwargs
                )
            )
            for i in reader if not i["Name"].startswith("#")
        ]
        for future in futures:
            results.append(future.result())
    return results
