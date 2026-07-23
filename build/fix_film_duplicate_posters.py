#!/usr/bin/env python3
import io
import os
import urllib.parse

import requests
from PIL import Image

import build_images as b

TMDB_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_KEY:
    raise RuntimeError("TMDB_API_KEY doit Ãªtre dÃ©fini dans .env ou dans l'environnement.")


def request_json(url):
    r = requests.get(url, headers={"User-Agent": b.UA}, timeout=20)
    r.raise_for_status()
    return r.json()


def request_bytes(url):
    r = requests.get(url, headers={"User-Agent": b.UA}, timeout=30)
    r.raise_for_status()
    return r.content


def save_movie(row, title, year):
    params = urllib.parse.urlencode({
        "api_key": TMDB_KEY,
        "language": "fr-FR",
        "query": title,
        "year": year,
    })
    data = request_json(f"https://api.themoviedb.org/3/search/movie?{params}")
    results = data.get("results") or []
    if not results:
        raise RuntimeError(f"TMDB introuvable: {title}")
    movie = results[0]
    poster = movie.get("poster_path")
    if not poster:
        raise RuntimeError(f"Affiche absente: {title}")

    thumb_data = request_bytes(f"https://image.tmdb.org/t/p/w342{poster}")
    full_data = request_bytes(f"https://image.tmdb.org/t/p/original{poster}")

    with Image.open(io.BytesIO(thumb_data)) as im:
        im.verify()
    with Image.open(io.BytesIO(full_data)) as im:
        im.verify()

    (b.THUMBS / "films").mkdir(parents=True, exist_ok=True)
    (b.FULL / "films").mkdir(parents=True, exist_ok=True)
    (b.THUMBS / "films" / f"{row}.webp").write_bytes(b.to_webp_thumb(thumb_data))
    (b.FULL / "films" / f"{row}.{b.raster_ext(full_data)}").write_bytes(full_data)
    print(f"films/{row}: {title} -> {poster}")


def main():
    save_movie("84", "HÃ¤xan", "1922")
    save_movie("121", "A Night at the Opera", "1935")
    save_movie("125", "Fury", "1936")
    save_movie("181", "Pather Panchali", "1955")
    save_movie("230", "The Last Picture Show", "1971")


if __name__ == "__main__":
    main()
