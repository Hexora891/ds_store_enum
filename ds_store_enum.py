#!/usr/bin/env python3

import requests
import os
import sys
import argparse
import time
import urllib3
from ds_store import DSStore
from collections import defaultdict

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RESET  = '\033[0m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
RED    = '\033[38;5;196m'
GREEN  = '\033[38;5;46m'
YELLOW = '\033[38;5;226m'
CYAN   = '\033[38;5;45m'
ORANGE = '\033[38;5;208m'
WHITE  = '\033[38;5;255m'
GRAY   = '\033[38;5;240m'
LBLUE  = '\033[38;5;75m'

def c(text, *codes):
    return ''.join(codes) + str(text) + RESET

visited    = set()
discovered = defaultdict(list)   # depth -> [full_url, ...]
stats      = {"checked": 0, "errors": 0}

def get_args():
    parser = argparse.ArgumentParser(
        description="Recursively enumerate paths via exposed .DS_Store files",
    )
    parser.add_argument('-u', '--url',     required=True, help='Target base URL')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Request timeout (default: 10s)')
    parser.add_argument('-o', '--output',  help='Write discovered paths to file')
    return parser.parse_args()

def divider():
    print(c("  " + "─" * 52, GRAY))

def fetch(url, timeout):
    stats["checked"] += 1
    return requests.get(f"{url}/.DS_Store", verify=False, timeout=timeout)

def save(content, fname):
    with open(fname, "wb") as f:
        f.write(content)

def parse(fname):
    entries = []
    with DSStore.open(fname) as d:
        for e in d:
            if e.filename not in entries and not e.filename.startswith('.'):
                entries.append(e.filename)
    return entries

def recurse(site_map, url, timeout, depth=0):
    if url in visited:
        return
    visited.add(url)

    batch = []
    for item in site_map:
        new_url = f"{url}/{item}"
        batch.append((item, new_url))

    # print this depth's batch
    if batch:
        divider()
        for item, new_url in batch:
            discovered[depth].append(new_url)
            print(c("  ", GRAY) + c(new_url, ORANGE))

    # recurse into each
    for item, new_url in batch:
        tmp = f".ds_tmp_{depth}_{item}"
        try:
            r = fetch(new_url, timeout)
            if r.status_code == 200:
                save(r.content, tmp)
                try:
                    children = parse(tmp)
                    recurse(children, new_url, timeout, depth + 1)
                finally:
                    if os.path.exists(tmp):
                        os.remove(tmp)
        except requests.exceptions.Timeout:
            stats["errors"] += 1
            print(c(f"  [timeout]  {new_url}", GRAY))
        except requests.exceptions.ConnectionError:
            stats["errors"] += 1
            print(c(f"  [error]    {new_url}", GRAY))
        except Exception as e:
            stats["errors"] += 1
            print(c(f"  [!] {e}", GRAY))

if __name__ == "__main__":
    args    = get_args()
    url     = args.url.rstrip('/')
    timeout = args.timeout
    index   = ".ds_store_index"

    print()
    print(c("  ds_store_enum", CYAN, BOLD) + c("  " + url, GRAY))
    print()

    # probe
    try:
        r = fetch(url, timeout)
    except Exception as e:
        print(c(f"  ✗  {e}", RED))
        sys.exit(1)

    if r.status_code != 200:
        print(c(f"  ✗  .DS_Store not found  (HTTP {r.status_code})", RED))
        print()
        sys.exit(0)

    print(c("  ✓  ", GREEN, BOLD) + c(".DS_Store found  ", WHITE) + c(f"{len(r.content)} bytes", CYAN, BOLD))
    print(c("  +  ", LBLUE, BOLD) + c("enumerating paths ...", GRAY))

    save(r.content, index)
    try:
        root_map = parse(index)
    except Exception as e:
        print(c(f"  ✗  parse error: {e}", RED))
        sys.exit(1)
    finally:
        if os.path.exists(index):
            os.remove(index)

    if not root_map:
        print(c("  !  no entries in root .DS_Store", YELLOW))
        sys.exit(0)

    # print root batch
    divider()
    for item in root_map:
        full = f"{url}/{item}"
        discovered[0].append(full)
        print(c("  ", GRAY) + c(full, ORANGE))

    recurse(root_map, url, timeout, depth=1)

    divider()
    print()

    # summary
    total = sum(len(v) for v in discovered.values())
    print(c("  ✓  ", GREEN, BOLD) + c(f"done  ", WHITE) + c(f"{total} paths  {stats['checked']} requests", GRAY) + (c(f"  {stats['errors']} errors", RED) if stats['errors'] else ""))
    print()

    if args.output:
        all_paths = [p for depth in sorted(discovered) for p in discovered[depth]]
        with open(args.output, "w") as f:
            f.write("\n".join(all_paths) + "\n")
        print(c(f"  →  saved to {args.output}", CYAN))
        print()
