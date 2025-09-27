import concurrent.futures

def run_parallel(reader, cmd, username, password, run_func):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                run_func,
                i["Name"],
                i["Host"],
                username if not i["Username"] else i["Username"],
                password if not i["Password"] else i["Password"],
                cmd
            )
            for i in reader if not i["Name"].startswith("#")
        ]
        for r in futures:
            results.append(r.result())
    return results
