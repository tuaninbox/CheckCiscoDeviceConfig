
import concurrent.futures
from .device import DeviceDataRetriever

def run_parallel(reader, cmd, username, password, run_func, filterlist=None, sanitizeconfig=True, removepassword: int = 15, **extra_kwargs):
    rows = list(reader)  # materialize reader so we can iterate multiple times
    results = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for row in rows:
            if row["Host"].startswith("#"):
                continue
            if filterlist and row["Host"].lower() not in filterlist:
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
                        sanitizeconfig=sanitizeconfig,
                        removepassword=removepassword,
                        **extra_kwargs
                    )
                )
            )

        for future in futures:
            results.append(future.result())

    return results
