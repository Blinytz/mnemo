#!/usr/bin/env python3
"""Print narrowly scoped media candidates from non-Wikimedia sources."""
import json
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen


UA = "MemoImagesAudit/1.0 (local educational PWA)"


def get_json(url):
    request = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(request, timeout=6) as response:
        return json.load(response)


def nasa(query):
    data = get_json("https://images-api.nasa.gov/search?" + urlencode({"q": query, "media_type": "image"}))
    rows = []
    for item in data.get("collection", {}).get("items", [])[:8]:
        info = (item.get("data") or [{}])[0]
        links = item.get("links") or []
        href = next((link.get("href") for link in links if link.get("render") == "image"), "")
        rows.append({"title": info.get("title"), "nasa_id": info.get("nasa_id"), "thumb": href})
    return rows


def archive(query):
    params = {
        "q": query,
        "fl[]": ["identifier", "title", "year", "mediatype"],
        "rows": 10,
        "output": "json",
    }
    data = get_json("https://archive.org/advancedsearch.php?" + urlencode(params, doseq=True))
    return data.get("response", {}).get("docs", [])


def books(query):
    data = get_json("https://www.googleapis.com/books/v1/volumes?" + urlencode({"q": query, "maxResults": 8}))
    rows = []
    for item in data.get("items", []):
        volume = item.get("volumeInfo", {})
        image = volume.get("imageLinks", {}).get("thumbnail", "")
        rows.append({"title": volume.get("title"), "authors": volume.get("authors"), "thumbnail": image})
    return rows


if __name__ == "__main__":
    terms = {
        "nasa": [
            "Prometheus moon", "Pandora moon", "Calypso moon", "Caliban moon", "Naiad moon",
            "Neptune moons Voyager 2", "Uranus moons discovery", "Caliban Uranus",
        ],
        "archive": [
            'title:("Le Christ marchant sur les eaux")',
            'title:("La Vie d un joueur")',
            'title:("Le Vol d un tableau")',
            'title:("Feat of Clay")',
        ],
        "books": ['intitle:"Hitchhiker\'s Guide to the Galaxy"'],
    }
    for source, queries in terms.items():
        print("\n###", source, flush=True)
        for query in queries:
            try:
                print("\n", query, flush=True)
                print(json.dumps(globals()[source](query), ensure_ascii=False, indent=2), flush=True)
            except Exception as exc:
                print("ERROR", exc, flush=True)
