#!/usr/bin/env python3
import requests

QUERIES = ["Chronos","Eros","Nike","Prometheus","Atlas","Medusa","Icarus","Daedalus","Narcissus","Echo","Pandora","Helios","Tyche","Aeolus","Medea","Hyperion"]


def main():
    for q in QUERIES:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": q,
            "gsrnamespace": "6",
            "gsrlimit": "10",
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
            "formatversion": "2",
        }
        r = requests.get("https://hades.fandom.com/api.php", params=params, headers={"User-Agent": "memo-local-builder/1.0"}, timeout=25)
        print("\n#", q, r.status_code)
        try:
            pages = r.json().get("query", {}).get("pages", [])
        except Exception as exc:
            print("JSONERR", exc)
            continue
        for p in pages:
            url = (p.get("imageinfo") or [{}])[0].get("url", "")
            print(p.get("title", ""), url[:120])


if __name__ == "__main__":
    main()
