#!/usr/bin/env python3
"""Ajoute les nouvelles entrees aux EXPANSION_LISTS dans memo.html."""
import pathlib, re, sys

REPO = pathlib.Path(__file__).parent.parent
HTML = REPO / 'memo.html'

Q = "'"  # apostrophe droite U+0027 uniquement

def row(*fields):
    return "[" + ",".join(Q + f.replace("\\", "\\\\").replace(Q, "\\'") + Q for f in fields) + "]"

NEW_CIVILISATIONS = [
    ("Carthage", "IXe–IIe si\xe8cle av. J.-C.", "Afrique du Nord", "Puissances maritimes et guerres puniques"),
    ("Empire perse ach\xe9m\xe9nide", "VIe–IVe si\xe8cle av. J.-C.", "Iran", "De Cyrus \xe0 Darius III"),
    ("Empire maurya", "IVe–IIe si\xe8cle av. J.-C.", "Inde", "Ashoka et diffusion du bouddhisme"),
    ("Dynastie Han", "206 av. J.-C.–220", "Chine", "Route de la Soie"),
    ("Empire perse sassanide", "224–651", "Iran", "Rival de Rome et de Byzance"),
    ("Empire gupta", "IVe–VIe si\xe8cle", "Inde", "\xc2ge d’or indien : math\xe9matiques, astronomie"),
    ("Califat abbasside", "750–1258", "Moyen-Orient", "\xc2ge d’or islamique"),
    ("Empire mongol", "XIIIe–XIVe si\xe8cle", "Eurasie", "Le plus vaste empire continental"),
    ("Empire ottoman", "1299–1922", "M\xe9diterran\xe9e orientale", "H\xe9ritier de Byzance"),
    ("Civilisation de Teotihuacan", "Ier–VIIe si\xe8cle", "Mexique central", "Pyramide du Soleil"),
    ("Nubie et M\xe9ro\xe9", "VIIIe s. av. J.-C.–IVe s.", "Soudan", "Royaume des pharaons noirs"),
    ("Empire de Songha\xef", "XVe–XVIe si\xe8cle", "Afrique de l’Ouest", "Tombouctou et manuscrits"),
    ("Empire moghol", "1526–1857", "Inde", "Taj Mahal et \xe2ge d’or culturel"),
    ("Japon f\xe9odal", "Xe–XIXe si\xe8cle", "Japon", "Samoura\xefs et shogunats"),
    ("Empire colonial britannique", "XVIe–XXe si\xe8cle", "Monde", "Le plus \xe9tendu de l’histoire"),
    ("Union sovi\xe9tique", "1922–1991", "Eurasie", "Superpuissance du XXe si\xe8cle"),
]

NEW_FLEUVES = [
    ("Niger", "4 185 km", "Afrique", "Golfe de Guin\xe9e"),
    ("Mackenzie", "4 241 km", "Am\xe9rique du Nord", "Mer de Beaufort"),
    ("Volga", "3 690 km", "Europe", "Mer Caspienne"),
    ("Zamb\xe8ze", "2 574 km", "Afrique", "Canal du Mozambique"),
    ("Orinoco", "2 410 km", "Am\xe9rique du Sud", "Atlantique"),
    ("Euphrate", "2 800 km", "Asie", "Chatt al-Arab"),
    ("Tigre", "1 900 km", "Asie", "Chatt al-Arab"),
    ("Gange", "2 525 km", "Asie", "Golfe du Bengale"),
    ("Indus", "3 180 km", "Asie", "Mer d’Arabie"),
    ("Murray", "2 375 km", "Australie", "Oc\xe9an Austral"),
    ("Danube", "2 860 km", "Europe", "Mer Noire"),
    ("Saint-Laurent", "1 197 km", "Am\xe9rique du Nord", "Atlantique"),
    ("Colorado", "2 330 km", "Am\xe9rique du Nord", "Golfe de Californie"),
    ("R\xedo Grande", "3 051 km", "Am\xe9rique du Nord", "Golfe du Mexique"),
    ("Orange", "2 200 km", "Afrique", "Atlantique"),
    ("Rhin", "1 230 km", "Europe", "Mer du Nord"),
    ("S\xe9n\xe9gal", "1 790 km", "Afrique", "Atlantique"),
    ("Irrawaddy", "2 170 km", "Asie", "Mer d’Andaman"),
]

NEW_COMPOSITEURS = [
    ("Johannes Brahms", "Romantisme", "Allemande", "Symphonie no 4"),
    ("Hector Berlioz", "Romantisme", "Fran\xe7aise", "Symphonie fantastique"),
    ("Piotr Tcha\xefkovski", "Romantisme", "Russe", "Le Lac des cygnes"),
    ("Gustav Mahler", "Post-romantisme", "Autrichienne", "Symphonies monumentales"),
    ("Giacomo Puccini", "Romantisme tardif", "Italienne", "La Boh\xe8me"),
    ("Franz Liszt", "Romantisme", "Hongroise", "Rhapsodies hongroises"),
    ("Robert Schumann", "Romantisme", "Allemande", "Sc\xe8nes d’enfants"),
    ("Sergue\xef Rachmaninov", "Post-romantisme", "Russe", "Concerto pour piano no 2"),
    ("Dmitri Chostakovitch", "XXe si\xe8cle", "Russe", "Symphonie no 5"),
    ("B\xe9la Bart\xf3k", "XXe si\xe8cle", "Hongroise", "Concerto pour orchestre"),
    ("Leonard Bernstein", "XXe si\xe8cle", "Am\xe9ricaine", "West Side Story"),
    ("Maurice Ravel", "Impressionnisme", "Fran\xe7aise", "Bol\xe9ro"),
    ("Gabriel Faur\xe9", "Romantisme", "Fran\xe7aise", "Requiem"),
    ("Camille Saint-Sa\xebns", "Romantisme", "Fran\xe7aise", "Le Carnaval des animaux"),
    ("Claudio Monteverdi", "Renaissance", "Italienne", "L’Orf\xe9o"),
    ("Edvard Grieg", "Romantisme", "Norv\xe9gienne", "Peer Gynt"),
    ("Jean Sibelius", "Romantisme tardif", "Finlandaise", "Finlandia"),
    ("Anton\xedn Dvoř\xe1k", "Romantisme", "Tch\xe8que", "Symphonie du Nouveau Monde"),
    ("Sergue\xef Prokofiev", "XXe si\xe8cle", "Russe", "Pierre et le Loup"),
    ("Aaron Copland", "XXe si\xe8cle", "Am\xe9ricaine", "Appalachian Spring"),
    ("Benjamin Britten", "XXe si\xe8cle", "Britannique", "Peter Grimes"),
    ("Philip Glass", "Contemporain", "Am\xe9ricaine", "Satyagraha"),
    ("Georges Bizet", "Romantisme", "Fran\xe7aise", "Carmen"),
    ("Henry Purcell", "Baroque", "Anglaise", "Didon et \xc9n\xe9e"),
    ("Christoph Willibald Gluck", "Classicisme", "Allemande", "Orph\xe9e et Eurydice"),
    ("Carl Maria von Weber", "Romantisme", "Allemande", "Le Freysch\xfctz"),
    ("Jean-Philippe Rameau", "Baroque", "Fran\xe7aise", "Les Indes galantes"),
]

NEW_CONSTELLATIONS = [
    ("Pers\xe9e", "Nord", "Mirfak", "Contient la variable Algol"),
    ("Androm\xe8de", "Nord", "Alpheratz", "Galaxie d’Androm\xe8de visible \xe0 l’œil nu"),
    ("Hercule", "Nord", "Kornephoros", "Amas globulaire M13"),
    ("Vierge", "C\xe9leste \xe9quatorial", "Spica", "Signe du zodiaque"),
    ("Balance", "C\xe9leste \xe9quatorial", "Zubenelgenubi", "Signe du zodiaque"),
    ("Verseau", "C\xe9leste \xe9quatorial", "Sadalsuud", "Signe du zodiaque"),
    ("B\xe9lier", "Nord", "Hamal", "Signe du zodiaque"),
    ("Cancer", "Nord", "Altarf", "Signe du zodiaque"),
    ("Capricorne", "Sud", "Deneb Algedi", "Signe du zodiaque"),
    ("Poissons", "C\xe9leste \xe9quatorial", "Eta Piscium", "Signe du zodiaque"),
    ("Centaure", "Sud", "Alpha Centauri", "\xc9toile la plus proche du Soleil"),
    ("Croix du Sud", "Sud", "Acrux", "Rep\xe8re de l’h\xe9misph\xe8re sud"),
    ("Dragon", "Nord", "Thuban", "Ancienne \xe9toile polaire"),
    ("P\xe9gase", "Nord", "Enif", "Grand Carr\xe9 de P\xe9gase"),
    ("Grand Chien", "C\xe9leste \xe9quatorial", "Sirius", "\xc9toile la plus brillante du ciel"),
    ("Petit Chien", "C\xe9leste \xe9quatorial", "Procyon", "Triangle d’hiver"),
    ("Cocher", "Nord", "Capella", "\xc9toile brillante du triangle d’hiver"),
    ("Bouvier", "Nord", "Arcturus", "\xc9toile la plus brillante de l’h\xe9misph\xe8re nord"),
    ("Couronne bor\xe9ale", "Nord", "Alphecca", "Arc de sept \xe9toiles"),
    ("Ophiuchus", "C\xe9leste \xe9quatorial", "Rasalhague", "13e signe officieux du zodiaque"),
    ("Hydre", "C\xe9leste \xe9quatorial", "Alphard", "La plus longue constellation du ciel"),
    ("\xc9ridain", "Sud", "Achernar", "Longue constellation m\xe9andreuse"),
    ("Corbeau", "Sud", "Gienah", "Petite constellation compacte"),
    ("Li\xe8vre", "Sud", "Arneb", "Sous les pieds d’Orion"),
    ("Ph\xe9nix", "Sud", "Ankaa", "Constellation australe brillante"),
    ("Serpent", "C\xe9leste \xe9quatorial", "Unukalhai", "Coup\xe9e en deux par Ophiuchus"),
]

NEW_SCIENTIFIQUES = [
    ("Euclide", "G\xe9om\xe9trie", "Grecque", "\xc9l\xe9ments de g\xe9om\xe9trie"),
    ("Hippocrate", "M\xe9decine", "Grecque", "P\xe8re de la m\xe9decine"),
    ("L\xe9onard de Vinci", "Sciences et arts", "Italienne", "Anatomie et machines volantes"),
    ("Johannes Kepler", "Astronomie", "Allemande", "Lois du mouvement plan\xe9taire"),
    ("Christiaan Huygens", "Physique", "N\xe9erlandaise", "Th\xe9orie des ondes lumineuses"),
    ("Carl von Linn\xe9", "Biologie", "Su\xe9doise", "Classification du vivant binominale"),
    ("Alessandro Volta", "Physique", "Italienne", "Invention de la pile \xe9lectrique"),
    ("Michael Faraday", "Physique", "Anglaise", "\xc9lectromagn\xe9tisme"),
    ("James Clerk Maxwell", "Physique", "\xc9cossaise", "\xc9quations de l’\xe9lectromagn\xe9tisme"),
    ("Louis Pasteur", "Microbiologie", "Fran\xe7aise", "Th\xe9orie des germes, vaccination"),
    ("Gregor Mendel", "G\xe9n\xe9tique", "Autrichienne", "Lois de l’h\xe9r\xe9dit\xe9"),
    ("Nikola Tesla", "Physique et ing\xe9nierie", "Serbo-am\xe9ricaine", "Courant alternatif"),
    ("Max Planck", "Physique", "Allemande", "Th\xe9orie des quanta"),
    ("Niels Bohr", "Physique", "Danoise", "Mod\xe8le atomique de Bohr"),
    ("Lise Meitner", "Physique nucl\xe9aire", "Austro-am\xe9ricaine", "Fission nucl\xe9aire"),
    ("Alan Turing", "Informatique", "Britannique", "Machine de Turing et intelligence artificielle"),
    ("Barbara McClintock", "G\xe9n\xe9tique", "Am\xe9ricaine", "Transposons (g\xe8nes sauteurs)"),
    ("Carl Sagan", "Astronomie et cosmologie", "Am\xe9ricaine", "Cosmos et vulgarisation scientifique"),
    ("Stephen Hawking", "Physique th\xe9orique", "Britannique", "Radiation de Hawking, trous noirs"),
    ("Tim Berners-Lee", "Informatique", "Britannique", "Invention du World Wide Web"),
    ("Tycho Brah\xe9", "Astronomie", "Danoise", "Mesures astronomiques de pr\xe9cision"),
    ("Robert Hooke", "Biologie et physique", "Anglaise", "D\xe9couverte des cellules (Micrographia)"),
    ("Dmitri Mend\xe9le\xefev", "Chimie", "Russe", "Tableau p\xe9riodique des \xe9l\xe9ments"),
    ("Werner Heisenberg", "Physique quantique", "Allemande", "Principe d’incertitude"),
    ("Francis Crick", "Biologie", "Britannique", "Co-d\xe9couverte de la structure de l’ADN"),
    ("James Watson", "Biologie", "Am\xe9ricaine", "Co-d\xe9couverte de la double h\xe9lice de l’ADN"),
]


def insert_after_last_item(html: str, list_id: str, last_item_name: str, new_items) -> str:
    """Trouve la derniere entree par son nom et insere apres."""
    # Cherche le dernier item dont le premier champ contient last_item_name
    escaped = re.escape(last_item_name)
    pat = re.compile(r"(\[" + re.escape(Q) + escaped + re.escape(Q) + r"(?:,[^\]]*)+\])")
    matches = list(pat.finditer(html))
    if not matches:
        print(f"  ⚠ Entree '{last_item_name}' non trouvee pour {list_id}", file=sys.stderr)
        return html
    m = matches[-1]  # derniere occurrence
    new_js = "".join("," + row(*item) for item in new_items)
    result = html[:m.end()] + new_js + html[m.end():]
    print(f"  + {len(new_items)} entrees apres '{last_item_name}' ({list_id})")
    return result


def main():
    html = HTML.read_text(encoding="utf-8")

    html = insert_after_last_item(html, "civilisations", "Empire inca", NEW_CIVILISATIONS)
    html = insert_after_last_item(html, "fleuves_monde", "M\xe9kong", NEW_FLEUVES)
    html = insert_after_last_item(html, "compositeurs", "Igor Stravinsky", NEW_COMPOSITEURS)
    html = insert_after_last_item(html, "constellations", "Lion", NEW_CONSTELLATIONS)
    html = insert_after_last_item(html, "grands_scientifiques", "Jane Goodall", NEW_SCIENTIFIQUES)

    HTML.write_text(html, encoding="utf-8")
    print(f"\n✓ {HTML.name} mis a jour")


if __name__ == "__main__":
    main()
