#!/usr/bin/env python3
import build_images as b

TITLES = [
    "Pandora (mythology)",
    "Daedalus",
    "Daedalus and Icarus",
    "Aeolus (son of Hippotes)",
    "Aeolus",
    "Ixion",
    "Hyperion (Titan)",
    "Hyperion (mythology)",
]


def main():
    b.load_cache()
    for title in TITLES:
        hit = b.wiki_batch([title], host="en.wikipedia.org", thumb_size=1600).get(title)
        if not hit:
            hit = b.wiki_search(title, host="en.wikipedia.org", thumb_size=1600)
        print("\n#", title)
        print(hit)


if __name__ == "__main__":
    main()
