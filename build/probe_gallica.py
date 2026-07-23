#!/usr/bin/env python3
"""Query Gallica's SRU endpoint for rare early-film illustrations."""
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


TERMS = [
    '"Le Christ marchant sur les eaux"',
    '"La Vie d’un joueur"',
    '"La Vie d\'un joueur"',
    '"Le Vol d’un tableau"',
    '"Feat of Clay"',
]


def search(term):
    query = quote(f'dc.title all {term}')
    url = f'https://gallica.bnf.fr/SRU?operation=searchRetrieve&version=1.2&query={query}&maximumRecords=10'
    request = Request(url, headers={'User-Agent': 'MemoImagesAudit/1.0'})
    with urlopen(request, timeout=10) as response:
        xml = response.read()
    root = ET.fromstring(xml)
    # Gallica's response namespaces vary; the textual record is sufficient to
    # expose Ark identifiers and titles without binding to a schema version.
    text = ET.tostring(root, encoding='unicode')
    snippets = []
    for token in text.split('ark:/'):
        if token == text.split('ark:/')[0]:
            continue
        ark = token.split('<', 1)[0].split('&', 1)[0]
        snippets.append('ark:/' + ark)
    return sorted(set(snippets))


for term in TERMS:
    try:
        print(term, '=>', search(term))
    except Exception as exc:
        print(term, '=> ERROR', exc)
