#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_images as b

REPO = Path(__file__).parent.parent


def write_raster(lid: str, n: str, tdata: bytes, fdata: bytes):
    thumb = b.to_webp_thumb(tdata)
    if not thumb:
        raise RuntimeError(f"thumb impossible: {lid}/{n}")
    full_ext = b.raster_ext(fdata)
    (b.THUMBS / lid).mkdir(parents=True, exist_ok=True)
    (b.FULL / lid).mkdir(parents=True, exist_ok=True)
    (b.THUMBS / lid / f"{n}.webp").write_bytes(thumb)
    (b.FULL / lid / f"{n}.{full_ext}").write_bytes(fdata)
    print(f"{lid}/{n}: full/{lid}/{n}.{full_ext}")


def write_svg_or_raster(lid: str, n: str, data: bytes, kind: str):
    (b.THUMBS / lid).mkdir(parents=True, exist_ok=True)
    (b.FULL / lid).mkdir(parents=True, exist_ok=True)
    if kind == "svg":
        (b.THUMBS / lid / f"{n}.svg").write_bytes(data)
        (b.FULL / lid / f"{n}.svg").write_bytes(data)
        print(f"{lid}/{n}: full/{lid}/{n}.svg")
    else:
        write_raster(lid, n, data, data)


def wiki(lid: str, n: str, title: str, host="en.wikipedia.org"):
    hit = b.wiki_batch([title], host=host, thumb_size=1600).get(title)
    if not hit:
        hit = b.wiki_search(title, host=host, thumb_size=1600)
    if not hit:
        raise RuntimeError(f"wiki introuvable: {lid}/{n} {title}")
    tdata, fdata = b.wiki_download(hit)
    if not tdata or not fdata:
        raise RuntimeError(f"download impossible: {lid}/{n} {title}")
    write_raster(lid, n, tdata, fdata)


def commons(lid: str, n: str, filename: str, width=1600):
    data, kind, found = b._download_commons_svg_or_thumb(filename, width=width)
    if not data:
        raise RuntimeError(f"commons introuvable: {lid}/{n} {filename}")
    write_svg_or_raster(lid, n, data, kind)


def tmdb(row: str, title: str, year: str = "", director: str = ""):
    tdata, fdata = b.resolve_tmdb(title, year, director, b.TMDB_KEY)
    if not tdata or not fdata:
        raise RuntimeError(f"tmdb introuvable: films/{row} {title}")
    write_raster("films", row, tdata, fdata)


def copy_existing(lid: str, src: str, dst: str):
    for ext in ("jpg", "png", "webp", "svg"):
        sp = b.FULL / lid / f"{src}.{ext}"
        if sp.exists():
            data = sp.read_bytes()
            if ext == "svg":
                (b.THUMBS / lid / f"{dst}.svg").write_bytes((b.THUMBS / lid / f"{src}.svg").read_bytes())
                (b.FULL / lid / f"{dst}.svg").write_bytes(data)
            else:
                tp = b.THUMBS / lid / f"{src}.webp"
                if tp.exists():
                    (b.THUMBS / lid / f"{dst}.webp").write_bytes(tp.read_bytes())
                else:
                    (b.THUMBS / lid / f"{dst}.webp").write_bytes(b.to_webp_thumb(data))
                (b.FULL / lid / f"{dst}.{ext}").write_bytes(data)
            print(f"{lid}/{dst}: copied from {src}")
            return
    raise RuntimeError(f"source absente: {lid}/{src}")


def main():
    b.load_cache()
    failures = []

    def run(label, fn, *args):
        try:
            fn(*args)
        except Exception as e:
            failures.append((label, str(e)))
            print(f"FAIL {label}: {e}")

    # F1
    run("f1 Jenson Button", wiki, "f1_champions", "60", "Jenson Button")

    # Département Nord localisation correcte.
    run("departement Nord localisation", commons, "departements", "60b", "Nord department location map.svg", 1600)

    # Films : corrections d'images ciblées, dont doublons remplacés dans clean_lists_for_app.
    film_targets = {
        "18": ("Alice Guy-Blaché", "fr.wikipedia.org"),
        "23": ("Pathé Frères", "fr.wikipedia.org"),
        "27": ("Pathé Frères", "fr.wikipedia.org"),
        "42": ("After Many Years (1908 film)", "en.wikipedia.org"),
        "49": ("L'Inferno", "en.wikipedia.org"),
        "121": ("Modern Times (film)", "en.wikipedia.org"),
        "125": ("La Grande Illusion", "fr.wikipedia.org"),
    }
    for row, (title, host) in film_targets.items():
        run(f"films {row} {title}", wiki, "films", row, title, host)
    run("films 219 Bonnie and Clyde", tmdb, "219", "Bonnie and Clyde", "1967", "Arthur Penn")
    run("films 288 Dances with Wolves", tmdb, "288", "Dances with Wolves", "1990", "Kevin Costner")
    run("films 368 Loveless", tmdb, "368", "Loveless", "2017", "Andrey Zvyagintsev")
    run("films 94 A Page of Madness", wiki, "films", "94", "A Page of Madness", "en.wikipedia.org")
    run("films 181 Pather Panchali", tmdb, "181", "Pather Panchali", "1955", "Satyajit Ray")
    run("films 230 The Last Picture Show", tmdb, "230", "The Last Picture Show", "1971", "Peter Bogdanovich")

    # Lune restante.
    run("lunes Nix", wiki, "lunes", "54", "Nix (moon)")

    # Mouvements picturaux.
    run("mouvements Post-Impressionism", wiki, "mouvements_peinture", "21", "Post-Impressionism")
    run("mouvements Surrealism", wiki, "mouvements_peinture", "33", "Surrealism")
    run("mouvements Abstract expressionism", wiki, "mouvements_peinture", "34", "Abstract expressionism")

    # Mythologie grecque.
    myth = {
        "18": "Chronos",
        "23": "Eros",
        "24": "Nike (mythology)",
        "25": "Prometheus",
        "26": "Atlas (mythology)",
        "41": "Medusa",
        "42": "Icarus",
        "43": "Daedalus",
        "44": "Narcissus (mythology)",
        "45": "Echo (mythology)",
        "48": "Pandora",
        "50": "Helios",
        "52": "Tyche",
        "53": "Aeolus",
        "55": "Medea",
        "59": "Hyperion (Titan)",
    }
    for row, title in myth.items():
        run(f"mythologie {row} {title}", wiki, "mythologie", row, title)

    # Os : images spécifiques quand possible, sinon schémas de groupe propres.
    os_targets = {
        "10": "Zygomatic bone",
        "11": "Palatine bone",
        "13": "Vomer",
        "15": "Malleus",
        "18": "Hyoid bone",
        "19": "Atlas (anatomy)",
        "40": "Lumbar vertebrae",
        "65": "Triquetrum",
        "68": "Trapezoid bone",
        "70": "Hamate bone",
        "71": "Metacarpal bones",
        "72": "Metacarpal bones",
        "74": "Metacarpal bones",
        "75": "Metacarpal bones",
        "77": "Phalanx bone",
        "79": "Phalanx bone",
        "80": "Phalanx bone",
        "83": "Phalanx bone",
        "85": "Phalanx bone",
        "86": "Phalanx bone",
        "89": "Phalanx bone",
        "98": "Talus bone",
        "100": "Cuneiform bones",
        "101": "Cuneiform bones",
        "103": "Cuboid bone",
        "106": "Metatarsal bones",
        "107": "Metatarsal bones",
        "108": "Metatarsal bones",
        "110": "Phalanx bone",
        "112": "Phalanx bone",
        "115": "Phalanx bone",
        "116": "Phalanx bone",
        "118": "Phalanx bone",
        "121": "Phalanx bone",
        "122": "Phalanx bone",
    }
    for row, title in os_targets.items():
        run(f"os {row} {title}", wiki, "os", row, title)

    # Périodes géologiques.
    run("periodes Neoproterozoic", wiki, "periodes_geologiques", "13", "Neoproterozoic")
    run("periodes Paleozoic", wiki, "periodes_geologiques", "16", "Paleozoic")
    run("periodes Mesozoic", wiki, "periodes_geologiques", "22", "Mesozoic")

    # Philosophes.
    philosophers = {
        "6": "Marcus Aurelius",
        "19": "Voltaire",
        "31": "Henri Bergson",
        "32": "Bertrand Russell",
        "39": "Claude Lévi-Strauss",
        "40": "Michel Foucault",
        "41": "Gilles Deleuze",
        "42": "Jacques Derrida",
    }
    for row, title in philosophers.items():
        run(f"philosophes {row} {title}", wiki, "philosophes", row, title)

    # XIXe / XXe.
    run("xixe 1820", wiki, "xixe", "20", "Revolutions of 1820")
    run("xxe 1911", wiki, "xxe", "12", "Amundsen's South Pole expedition")

    b.save_cache()
    if failures:
        report = b.BUILD_DIR / "priority_failures.txt"
        report.write_text("\n".join(f"{k}: {v}" for k, v in failures), encoding="utf-8")
        print(f"Failures: {len(failures)} -> {report}")


if __name__ == "__main__":
    main()
