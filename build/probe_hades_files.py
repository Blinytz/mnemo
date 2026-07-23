#!/usr/bin/env python3
import json
import subprocess
import urllib.parse

import requests

FILES = ["Chronos.png","Eros.png","Nike.png","Prometheus.png","Atlas.png","Medusa.png","Icarus.png","Daedalus.png","Narcissus.png","Echo.png","Pandora.png","Helios.png","Tyche.png","Aeolus.png","Medea.png","Hyperion.png"]


def main():
    for f in FILES:
        title = "File:" + f
        params = {
            "action": "query",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
            "formatversion": "2",
        }
        r = requests.get("https://hades.fandom.com/api.php", params=params, headers={"User-Agent": "memo-local-builder/1.0"}, timeout=20)
        status = r.status_code
        url = ""
        try:
            pages = r.json().get("query", {}).get("pages", [])
            url = pages[0].get("imageinfo", [{}])[0].get("url", "") if pages else ""
        except Exception as exc:
            url = f"JSONERR {exc}"
        print(f, status, url[:160])


if __name__ == "__main__":
    main()
