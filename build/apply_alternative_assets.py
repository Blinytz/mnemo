#!/usr/bin/env python3
"""Apply vetted NASA and Open Library assets without re-running broad batches."""
import json
import sys
from urllib.request import Request, urlopen

import build_images as b
from fix_visual_quality_v60 import image_map, write_replacement


NASA_TARGETS = [
    ("lunes", "22", "PIA17207", "Prometheus Up Close"),
    ("lunes", "23", "PIA12690", "Flying by Pandora"),
    ("lunes", "28", "PIA12598", "Calypso Close Up"),
]
DIRECT_TARGETS = [
    ("litterature", "56", "https://covers.openlibrary.org/b/isbn/0345391802-L.jpg", "Open Library ISBN 0345391802"),
]
UA = "MemoImagesAudit/1.0 (local educational PWA)"


def nasa_original(nasa_id):
    request = Request(f"https://images-api.nasa.gov/asset/{nasa_id}", headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(request, timeout=12) as response:
        data = json.load(response)
    urls = [item.get("href", "") for item in data.get("collection", {}).get("items", [])]
    # NASA returns the original, TIFFs, and derivative JPEGs. A largest JPEG is
    # predictable to decode locally and more than sufficient for full display.
    jpeg = [url for url in urls if url.lower().endswith((".jpg", ".jpeg"))]
    if not jpeg:
        return None, None
    preferred = next((url for url in jpeg if "~orig" in url), jpeg[-1])
    return direct_image(preferred), preferred


def direct_image(url):
    request = Request(url, headers={"User-Agent": UA, "Accept": "image/*"})
    try:
        with urlopen(request, timeout=12) as response:
            data = response.read()
    except Exception:
        return None
    return data if b.verify_image(data) else None


def main():
    mapping = image_map()
    failures = []
    done = []
    for list_id, row, nasa_id, title in NASA_TARGETS:
        try:
            data, url = nasa_original(nasa_id)
            if not data:
                raise RuntimeError("asset NASA indisponible")
            done.append(write_replacement(mapping, list_id, row, data, f"NASA:{nasa_id}:{title}:{url}"))
            print(f"OK {list_id}/{row} <- NASA {nasa_id}")
        except Exception as exc:
            failures.append((list_id, row, str(exc)))
            print(f"FAIL {list_id}/{row}: {exc}")
    for list_id, row, url, source in DIRECT_TARGETS:
        try:
            data = direct_image(url)
            if not data:
                raise RuntimeError("couverture indisponible")
            done.append(write_replacement(mapping, list_id, row, data, source))
            print(f"OK {list_id}/{row} <- {source}")
        except Exception as exc:
            failures.append((list_id, row, str(exc)))
            print(f"FAIL {list_id}/{row}: {exc}")
    print(json.dumps({"completed": done, "failures": failures}, ensure_ascii=False, indent=2))
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
