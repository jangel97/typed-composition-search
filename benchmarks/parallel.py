from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_QUERY_WORKERS = 4


def run_queries_parallel(queries, process_fn, max_workers=DEFAULT_QUERY_WORKERS):
    if max_workers <= 1:
        return [process_fn(q) for q in queries]

    results = [None] * len(queries)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {pool.submit(process_fn, q): i for i, q in enumerate(queries)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()
    return results
