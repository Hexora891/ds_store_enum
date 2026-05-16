# ds_store_enum

A recursive `.DS_Store` file enumerator for web servers. Discovers exposed directory structure by parsing Apple `.DS_Store` metadata files left behind on misconfigured servers, then recursively follows each discovered path to map the full site tree.

---

## How it works

macOS creates a `.DS_Store` file in every directory a user browses in Finder. When developers deploy web applications from a Mac without cleaning up, these files get uploaded alongside the application. Because `.DS_Store` is a binary index of directory contents, anyone who can fetch it gains a complete listing of files and folders that exist at that path — regardless of whether directory listing is enabled on the server.

`ds_store_enum` automates this:

1. Checks if `/.DS_Store` is accessible at the target
2. Parses the binary file to extract directory and file names
3. Requests `.DS_Store` at each discovered path
4. Repeats recursively until no further `.DS_Store` files are found

---

## Installation

**Requirements:** Python 3.7+

```bash
git clone https://github.com/youruser/ds_store_enum
cd ds_store_enum
pip install -r requirements.txt
```

`requirements.txt`

```
requests
ds-store
urllib3
```

---

## Usage

```
python3 ds_enum.py -u <url> [-t <timeout>] [-o <output>]
```

| Flag | Long | Description | Default |
|------|------|-------------|---------|
| `-u` | `--url` | Target base URL | required |
| `-t` | `--timeout` | Request timeout in seconds | `10` |
| `-o` | `--output` | Write discovered paths to file | — |

---

## Examples

**Basic scan**
```bash
python3 ds_enum.py -u http://10.13.38.11
```

**Save results to file**
```bash
python3 ds_enum.py -u http://10.13.38.11 -o paths.txt
```

**Custom timeout**
```bash
python3 ds_enum.py -u http://10.13.38.11 -t 5 -o results.txt
```

**Scan a subdirectory directly**
```bash
python3 ds_enum.py -u http://10.13.38.11/dev
```

---

## Sample output

```
  ds_store_enum  http://10.13.38.11

  ✓  .DS_Store found  10244 bytes
  +  enumerating paths ...
  ────────────────────────────────────────────────────────
  http://10.13.38.11/admin
  http://10.13.38.11/dev
  http://10.13.38.11/Images
  http://10.13.38.11/JS
  http://10.13.38.11/Plugins
  http://10.13.38.11/Templates
  http://10.13.38.11/Themes
  http://10.13.38.11/Uploads
  http://10.13.38.11/Widgets
  http://10.13.38.11/web.config
  ────────────────────────────────────────────────────────
  http://10.13.38.11/dev/304c0c90fbc6520610abbf378e2339d1
  http://10.13.38.11/dev/dca66d38fd916317687e1390a420c3fc
  ────────────────────────────────────────────────────────
  http://10.13.38.11/dev/304c0c90fbc6520610abbf378e2339d1/core
  http://10.13.38.11/dev/304c0c90fbc6520610abbf378e2339d1/db
  http://10.13.38.11/dev/304c0c90fbc6520610abbf378e2339d1/src
  ────────────────────────────────────────────────────────
  http://10.13.38.11/Widgets/Framework/Layouts/custom
  http://10.13.38.11/Widgets/Framework/Layouts/default
  ────────────────────────────────────────────────────────

  ✓  done  50 paths  37 requests
```

Paths are printed in discovery order, grouped by depth level and separated by dividers. Each group represents one `.DS_Store` parse — so the grouping reflects the actual directory hierarchy.

---

## Detection & remediation

**For defenders:** this tool will generate sequential `GET /.DS_Store` requests across multiple paths from a single IP. These appear in access logs as `200 OK` responses for `.DS_Store` files. Any `.DS_Store` being served with a `200` is a misconfiguration.

**To remediate:**
- Add a rule to your web server config to block `.DS_Store` files:

  *Nginx*
  ```nginx
  location ~ /\.DS_Store {
      deny all;
      return 404;
  }
  ```

  *Apache*
  ```apache
  <FilesMatch "^\.DS_Store$">
      Require all denied
  </FilesMatch>
  ```

- Add `.DS_Store` to your `.gitignore` and audit existing repositories for committed `.DS_Store` files.

---

## Disclaimer

This tool is intended for authorized security testing and CTF environments only. Do not use against systems you do not have explicit permission to test.