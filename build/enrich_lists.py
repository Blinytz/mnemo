#!/usr/bin/env python3
"""Enrichit les listes creuses dans memo.html."""
import re, json, pathlib, sys

REPO = pathlib.Path(__file__).parent.parent
HTML = REPO / 'memo.html'

# ─── Nouvelles entrées EXPANSION_LISTS ────────────────────────────────────
# Format : [nom, col3, col4, col5]  (col1=Numéro, col2=Image auto)

NEW_CIVILISATIONS = [
    ["Carthage", "IXe–IIe siècle av. J.-C.", "Afrique du Nord", "Puissances maritimes et guerres puniques"],
    ["Empire perse achéménide", "VIe–IVe siècle av. J.-C.", "Iran", "De Cyrus à Darius III"],
    ["Empire maurya", "IVe–IIe siècle av. J.-C.", "Inde", "Ashoka et diffusion du bouddhisme"],
    ["Dynastie Han", "206 av. J.-C.–220", "Chine", "Route de la Soie"],
    ["Empire perse sassanide", "224–651", "Iran", "Rival de Rome et de Byzance"],
    ["Empire gupta", "IVe–VIe siècle", "Inde", "Âge d’or indien : mathématiques, astronomie"],
    ["Califat abbasside", "750–1258", "Moyen-Orient", "Âge d’or islamique"],
    ["Empire mongol", "XIIIe–XIVe siècle", "Eurasie", "Le plus vaste empire continental"],
    ["Empire ottoman", "1299–1922", "Méditerranée orientale", "Héritier de Byzance"],
    ["Civilisation de Teotihuacan", "Ier–VIIe siècle", "Mexique central", "Pyramide du Soleil"],
    ["Nubie et Méroé", "VIIIe siècle av. J.-C.–IVe siècle", "Soudan", "Royaume des pharaons noirs"],
    ["Empire de Songhaï", "XVe–XVIe siècle", "Afrique de l’Ouest", "Tombouctou et manuscrits"],
    ["Empire moghol", "1526–1857", "Inde", "Taj Mahal et âge d’or culturel"],
    ["Japon féodal", "Xe–XIXe siècle", "Japon", "Samouraïs et shogunats"],
    ["Empire colonial britannique", "XVIe–XXe siècle", "Monde", "Le plus étendu de l’histoire"],
    ["Union soviétique", "1922–1991", "Eurasie", "Superpuissance du XXe siècle"],
]

NEW_FLEUVES = [
    ["Niger", "4 185 km", "Afrique", "Golfe de Guinée"],
    ["Mackenzie", "4 241 km", "Amérique du Nord", "Mer de Beaufort"],
    ["Volga", "3 690 km", "Europe", "Mer Caspienne"],
    ["Zambèze", "2 574 km", "Afrique", "Canal du Mozambique"],
    ["Orinoco", "2 410 km", "Amérique du Sud", "Atlantique"],
    ["Euphrate", "2 800 km", "Asie", "Chatt al-Arab"],
    ["Tigre", "1 900 km", "Asie", "Chatt al-Arab"],
    ["Gange", "2 525 km", "Asie", "Golfe du Bengale"],
    ["Indus", "3 180 km", "Asie", "Mer d’Arabie"],
    ["Murray", "2 375 km", "Australie", "Océan Austral"],
    ["Danube", "2 860 km", "Europe", "Mer Noire"],
    ["Saint-Laurent", "1 197 km", "Amérique du Nord", "Atlantique"],
    ["Colorado", "2 330 km", "Amérique du Nord", "Golfe de Californie"],
    ["Río Grande", "3 051 km", "Amérique du Nord", "Golfe du Mexique"],
    ["Orange", "2 200 km", "Afrique", "Atlantique"],
    ["Rhin", "1 230 km", "Europe", "Mer du Nord"],
    ["Sénégal", "1 790 km", "Afrique", "Atlantique"],
    ["Vénisséi (Ienisseï)", "5 539 km", "Asie", "Océan Arctique"],
]

NEW_COMPOSITEURS = [
    ["Johannes Brahms", "Romantisme", "Allemande", "Symphonie no 4"],
    ["Hector Berlioz", "Romantisme", "Française", "Symphonie fantastique"],
    ["Piotr Tchaïkovski", "Romantisme", "Russe", "Le Lac des cygnes"],
    ["Gustav Mahler", "Post-romantisme", "Autrichienne", "Symphonies monumentales"],
    ["Giacomo Puccini", "Romantisme tardif", "Italienne", "La Bohème"],
    ["Franz Liszt", "Romantisme", "Hongroise", "Rhapsodies hongroises"],
    ["Robert Schumann", "Romantisme", "Allemande", "Scènes d’enfants"],
    ["Sergueï Rachmaninov", "Post-romantisme", "Russe", "Concerto pour piano no 2"],
    ["Dmitri Chostakovitch", "XXe siècle", "Russe", "Symphonie no 5"],
    ["Béla Bartók", "XXe siècle", "Hongroise", "Concerto pour orchestre"],
    ["Leonard Bernstein", "XXe siècle", "Américaine", "West Side Story"],
    ["Maurice Ravel", "Impressionnisme", "Française", "Boléro"],
    ["Gabriel Fauré", "Romantisme", "Française", "Requiem"],
    ["Camille Saint-Saëns", "Romantisme", "Française", "Le Carnaval des animaux"],
    ["Claudio Monteverdi", "Renaissance", "Italienne", "L’Orféo"],
    ["Edvard Grieg", "Romantisme", "Norvégienne", "Peer Gynt"],
    ["Jean Sibelius", "Romantisme tardif", "Finlandaise", "Finlandia"],
    ["Antonín Dvořák", "Romantisme", "Tchèque", "Symphonie du Nouveau Monde"],
    ["Sergueï Prokofiev", "XXe siècle", "Russe", "Pierre et le Loup"],
    ["Aaron Copland", "XXe siècle", "Américaine", "Appalachian Spring"],
    ["Benjamin Britten", "XXe siècle", "Britannique", "Peter Grimes"],
    ["Philip Glass", "Contemporain", "Américaine", "Satyagraha"],
    ["Georges Bizet", "Romantisme", "Française", "Carmen"],
    ["Henry Purcell", "Baroque", "Anglaise", "Didon et Énée"],
    ["Christoph Willibald Gluck", "Classicisme", "Allemande", "Orphée et Eurydice"],
    ["Carl Maria von Weber", "Romantisme", "Allemande", "Le Freischütz"],
    ["Jean-Philippe Rameau", "Baroque", "Française", "Les Indes galantes"],
    ["Henry Berlioz", "Romantisme", "Française", "La Damnation de Faust"],
]
# Dédoublonnage Berlioz
NEW_COMPOSITEURS = [c for c in NEW_COMPOSITEURS if c[0] != "Henry Berlioz"]

NEW_CONSTELLATIONS = [
    ["Persée", "Nord", "Mirfak", "Contient la variable Algol"],
    ["Andromède", "Nord", "Alpheratz", "Galaxie d’Andromède visible à l’œil nu"],
    ["Hercule", "Nord", "Kornephoros", "Amas globulaire M13"],
    ["Vierge", "Céleste équatorial", "Spica", "Signe du zodiaque"],
    ["Balance", "Céleste équatorial", "Zubenelgenubi", "Signe du zodiaque"],
    ["Verseau", "Céleste équatorial", "Sadalsuud", "Signe du zodiaque"],
    ["Bélier", "Nord", "Hamal", "Signe du zodiaque"],
    ["Cancer", "Nord", "Altarf", "Signe du zodiaque"],
    ["Capricorne", "Sud", "Deneb Algedi", "Signe du zodiaque"],
    ["Poissons", "Céleste équatorial", "Eta Piscium", "Signe du zodiaque"],
    ["Centaure", "Sud", "Alpha Centauri", "Étoile la plus proche du Soleil"],
    ["Croix du Sud", "Sud", "Acrux", "Repère de l’hémisphère sud"],
    ["Dragon", "Nord", "Thuban", "Ancienne étoile polaire"],
    ["Pégase", "Nord", "Enif", "Grand Carré de Pégase"],
    ["Grand Chien", "Céleste équatorial", "Sirius", "Étoile la plus brillante du ciel"],
    ["Petit Chien", "Céleste équatorial", "Procyon", "Triangle d’hiver"],
    ["Cocher", "Nord", "Capella", "Étoile brillante du triangle d’hiver"],
    ["Bouvier", "Nord", "Arcturus", "Étoile la plus brillante de l’hémisphère nord"],
    ["Couronne boréale", "Nord", "Alphecca", "Arc de sept étoiles"],
    ["Ophiuchus", "Céleste équatorial", "Rasalhague", "13e signe officieux du zodiaque"],
    ["Hydre", "Céleste équatorial", "Alphard", "La plus longue constellation du ciel"],
    ["Éridain", "Sud", "Achernar", "Longue constellation méandreuse"],
    ["Corbeau", "Sud", "Gienah", "Petite constellation compacte"],
    ["Lièvre", "Sud", "Arneb", "Sous les pieds d’Orion"],
    ["Phénix", "Sud", "Ankaa", "Constellation australe brillante"],
    ["Serpent", "Céleste équatorial", "Unukalhai", "Coupée en deux par Ophiuchus"],
]

NEW_SCIENTIFIQUES = [
    ["Euclide", "Géométrie", "Grecque", "Éléments de géométrie"],
    ["Hippocrate", "Médecine", "Grecque", "Père de la médecine"],
    ["Léonard de Vinci", "Sciences et arts", "Italienne", "Anatomie et machines volantes"],
    ["Johannes Kepler", "Astronomie", "Allemande", "Lois du mouvement planétaire"],
    ["Christiaan Huygens", "Physique", "Néerlandaise", "Théorie des ondes lumineuses"],
    ["Carl von Linné", "Biologie", "Suédoise", "Classification du vivant binominale"],
    ["Alessandro Volta", "Physique", "Italienne", "Invention de la pile électrique"],
    ["Michael Faraday", "Physique", "Anglaise", "Électromagnétisme"],
    ["James Clerk Maxwell", "Physique", "Écossaise", "Équations de l’électromagnétisme"],
    ["Louis Pasteur", "Microbiologie", "Française", "Théorie des germes, vaccination"],
    ["Gregor Mendel", "Génétique", "Autrichienne", "Lois de l’hérédité"],
    ["Nikola Tesla", "Physique / ingénierie", "Serbo-américaine", "Courant alternatif"],
    ["Max Planck", "Physique", "Allemande", "Théorie des quanta"],
    ["Niels Bohr", "Physique", "Danoise", "Modèle atomique de Bohr"],
    ["Lise Meitner", "Physique nucléaire", "Austro-américaine", "Fission nucléaire"],
    ["Alan Turing", "Informatique", "Britannique", "Machine de Turing et intelligence artificielle"],
    ["Barbara McClintock", "Génétique", "Américaine", "Transposons (gènes sauteurs)"],
    ["Carl Sagan", "Astronomie / cosmologie", "Américaine", "Cosmos et vulgarisation scientifique"],
    ["Stephen Hawking", "Physique théorique", "Britannique", "Radiation de Hawking, trous noirs"],
    ["Tim Berners-Lee", "Informatique", "Britannique", "Invention du World Wide Web"],
    ["Tycho Brahé", "Astronomie", "Danoise", "Mesures astronomiques de précision"],
    ["Robert Hooke", "Biologie / physique", "Anglaise", "Découverte des cellules (Micrographia)"],
    ["Dmitri Mendéleïev", "Chimie", "Russe", "Tableau périodique des éléments"],
    ["Werner Heisenberg", "Physique quantique", "Allemande", "Principe d’incertitude"],
    ["Francis Crick", "Biologie", "Britannique", "Co-découverte de la structure de l’ADN"],
    ["James Watson", "Biologie", "Américaine", "Co-découverte de la double hélice de l’ADN"],
]

# ─── Nouvelles lignes CURATED_LISTS_V3 ────────────────────────────────────
# Format : [Bataille, Date, Lieu, Issue]

NEW_BATAILLES = [
    ["Gaugamèles", "331 av. J.-C.", "Perse (Irak actuel)", "Victoire d’Alexandre, fin de l’Empire perse"],
    ["Cannæ", "216 av. J.-C.", "Italie du Sud", "Victoire d’Hannibal, encerclement romain"],
    ["Actium", "31 av. J.-C.", "Grèce", "Victoire d’Octave, fin de la République romaine"],
    ["Châlons", "451", "France", "Arrêt d’Attila en Occident"],
    ["Yarmouk", "636", "Syrie", "Conquête arabo-musulmane du Proche-Orient"],
    ["Poitiers", "732", "France", "Arrêt de l’expansion arabe en Europe"],
    ["Lépante", "1571", "Méditerranée", "Arrêt de l’expansion ottomane"],
    ["Rocroi", "1643", "France", "Fin de l’hégémonie espagnole"],
    ["Poltava", "1709", "Ukraine", "Victoire de Pierre le Grand sur Charles XII"],
    ["Plassey", "1757", "Inde", "Domination britannique en Inde"],
    ["Yorktown", "1781", "États-Unis", "Indépendance américaine confirmée"],
    ["Valmy", "1792", "France", "Première victoire de la Révolution française"],
    ["Austerlitz", "1805", "Moravie", "Chef-d’œuvre tactique napoléonien"],
    ["Leipzig", "1813", "Allemagne", "Défaite de Napoléon, début de sa fin"],
    ["Tsushima", "1905", "Mer du Japon", "Victoire japonaise sur la flotte russe"],
    ["La Marne", "1914", "France", "Arrêt de l’avance allemande"],
    ["La Somme", "1916", "France", "Offensive alliée (1 200 000 victimes)"],
    ["El-Alamein", "1942", "Égypte", "Tournant en Afrique du Nord"],
    ["Koursk", "1943", "URSS", "Plus grande bataille de chars de l’histoire"],
    ["Normandie (D-Day)", "1944", "France", "Débarquement allié, libération de l’Europe"],
    ["Berlin", "1945", "Allemagne", "Fin de la guerre en Europe"],
    ["Inchon", "1950", "Corée", "Contre-offensive MacArthur"],
    ["Kippour", "1973", "Moyen-Orient", "Guerre israélo-arabe, choc pétrolier"],
    ["Falklands", "1982", "Atlantique Sud", "Victoire britannique, chute de la junte argentine"],
    ["Golfe Persique", "1991", "Iraëk", "Libération du Koweït (coalition ONU)"],
]

NEW_EXPLORATIONS = [
    ["Ibn Battuta", "1325–1354", "Afrique, Asie, Europe", "Plus de 120 000 km de voyages"],
    ["Bartolomeu Dias", "1487–1488", "Afrique", "Premier contournement du cap de Bonne-Espérance"],
    ["Amerigo Vespucci", "1499–1504", "Amériques", "Reconnaissance d’un nouveau continent"],
    ["Hernán Cortés", "1519–1521", "Mexique", "Conquête de l’Empire aztèque"],
    ["Francisco Pizarro", "1531–1533", "Pérou", "Conquête de l’Empire inca"],
    ["Jacques Cartier", "1534–1542", "Canada", "Exploration du fleuve Saint-Laurent"],
    ["Francis Drake", "1577–1580", "Monde", "Deuxième circumnavigation mondiale"],
    ["Samuel de Champlain", "1603–1615", "Canada", "Fondation de Québec en 1608"],
    ["Abel Tasman", "1642–1644", "Océanie", "Découverte de la Tasmanie et de la Nouvelle-Zélande"],
    ["Mungo Park", "1795–1806", "Afrique", "Exploration du fleuve Niger"],
    ["Lewis et Clark", "1804–1806", "Amérique du Nord", "Traversée des États-Unis jusqu’au Pacifique"],
    ["René Caillié", "1827–1828", "Afrique", "Premier Européen à revenir de Tombouctou"],
    ["Ernest Shackleton", "1914–1916", "Antarctique", "Survie après le naufrage de l’Endurance"],
    ["Edmund Hillary et Tenzing Norgay", "1953", "Himalaya", "Premier sommet de l’Everest"],
    ["Jacques Piccard et Don Walsh", "1960", "Fosse des Mariannes", "Profondeur maximale : 10 916 m"],
    ["Neil Armstrong", "1969", "Lune", "Premiers pas humains sur la Lune"],
    ["Valentina Teréchkova", "1963", "Espace", "Première femme dans l’espace"],
]

NEW_MONTAGNES = [
    ["Lhotse", "8 516 m", "Himalaya", "Népal / Chine"],
    ["Makalu", "8 485 m", "Himalaya", "Népal / Chine"],
    ["Cho Oyu", "8 188 m", "Himalaya", "Chine / Népal"],
    ["Dhaulagiri", "8 167 m", "Himalaya", "Népal"],
    ["Manaslu", "8 163 m", "Himalaya", "Népal"],
    ["Nanga Parbat", "8 126 m", "Himalaya occidental", "Pakistan"],
    ["Annapurna", "8 091 m", "Himalaya", "Népal"],
    ["Mont Elbrouz", "5 642 m", "Caucase", "Russie (point culminant d’Europe)"],
    ["Puncak Jaya", "4 884 m", "Nouvelle-Guinée", "Indonésie (point culminant d’Océanie)"],
    ["Mont Vinson", "4 892 m", "Antarctique", "Point culminant de l’Antarctique"],
    ["Mont Logan", "5 959 m", "Saint-Élias", "Canada (point culminant)"],
    ["Ojos del Salado", "6 893 m", "Andes", "Chili / Argentine (volcan le plus haut du monde)"],
    ["Fujiyama", "3 776 m", "Honshū", "Japon"],
    ["Vésuve", "1 281 m", "Campanie", "Italie (destruction de Pompéi en 79)"],
    ["Mont Olympe", "2 917 m", "Thessalie", "Grèce (demeure des dieux)"],
    ["Popocatepetl", "5 426 m", "Axe néovolcanique", "Mexique"],
    ["Table Mountain", "1 086 m", "Afrique du Sud", "Cap-Occidental"],
    ["Ben Nevis", "1 345 m", "Grampians", "Royaume-Uni (point culminant)"],
    ["Aneto", "3 404 m", "Pyrénées", "Espagne (point culminant des Pyrénées)"],
    ["Teide", "3 718 m", "Îles Canaries", "Espagne"],
    ["Grand Teton", "4 199 m", "Rocheuses", "États-Unis"],
    ["Montagne Sainte-Hélène", "2 549 m", "Cascades", "États-Unis (volcan actif)"],
]

NEW_DETROITS = [
    ["Pas-de-Calais", "Manche et mer du Nord", "France et Angleterre", "Détroit le plus fréquenté au monde"],
    ["Messine", "Méditerranée et mer Tyrrhénienne", "Sicile et Italie", "Charybde et Scylla mythologiques"],
    ["Skagerrak", "Mer du Nord et Kattegat", "Danemark, Norvège, Suède", "Sortie de la Baltique"],
    ["Taïwan", "Mer de Chine méridionale et orientale", "Chine et Taïwan", "Tension géopolitique majeure"],
    ["Corée", "Mer du Japon et mer de Chine orientale", "Corée et Japon", "Île de Tsushima"],
    ["Lombok", "Mer de Java et mer de Flores", "Bali et Lombok", "Ligne de Wallace biogéographique"],
    ["Bass", "Océan Indien et mer de Tasman", "Australie et Tasmanie", "Traversée tempêtueuse"],
    ["Floride", "Atlantique et golfe du Mexique", "États-Unis et Cuba", "Passage stratégique des Amériques"],
    ["Øresund", "Kattegat et mer Baltique", "Danemark et Suède", "Pont Øresund"],
    ["Mozambique", "Canal du Mozambique", "Afrique et Madagascar", "Route des tankers"],
    ["Singapour", "Mer de Chine méridionale et détroit de Malacca", "Malaisie et Singapour", "Extension du détroit de Malacca"],
    ["Tokugawa (Tsugaru)", "Mer du Japon et Pacifique", "Honshu et Hokkaido", "Sépare les deux principales îles du Japon"],
]

NEW_PARCS = [
    ["Grand Canyon", "États-Unis", "1919", "Canyon du Colorado"],
    ["Galápagos", "Équateur", "1959", "Tortues géantes et iguanes marins"],
    ["Iguaçu", "Argentine / Brésil", "1934", "Chutes d’Iguaçu"],
    ["Everglades", "États-Unis", "1947", "Zones humides de Floride et lamantins"],
    ["Récif de la Grande Barrière", "Australie", "1975", "Plus grand récif corallien du monde"],
    ["Vanoise", "France", "1963", "Premier parc national français"],
    ["Grand Paradis", "Italie", "1922", "Bouquetins des Alpes"],
    ["Virunga", "RDC", "1925", "Gorilles de montagne"],
    ["Sagarmatha", "Népal", "1976", "Parc de l’Everest"],
    ["Jiuzhaigou", "Chine", "1978", "Lacs aux cinq couleurs"],
    ["Sundarbans", "Bangladesh / Inde", "1984", "Mangroves et tigres du Bengale"],
    ["Kaziranga", "Inde", "1974", "Rhinocéros unicornes"],
    ["Denali", "États-Unis", "1917", "Sommet de l’Amérique du Nord"],
    ["Cévennes", "France", "1970", "Paysages caussenards et méditerranéens"],
    ["Pyrénées", "France", "1967", "Ours bruns et isards"],
    ["Pantanal", "Brésil", "1981", "Plus grande zone humide du monde"],
    ["Okavango", "Botswana", "2019", "Delta intérieur aux 30 000 éléphants"],
    ["Białowieża", "Pologne / Biélorussie", "1932", "Dernière forêt primaire d’Europe"],
    ["Simien", "Éthiopie", "1969", "Babouins gelada et loups d’Abyssinie"],
    ["Bwindi", "Ouganda", "1991", "La moitié des gorilles de montagne du monde"],
    ["Wrangell-Saint-Élias", "États-Unis", "1980", "Plus grand parc américain"],
    ["Dolomites", "Italie", "2009", "UNESCO : falaises calcaires verticales"],
]

NEW_ARCHITECTES = [
    ["Michelangelo Buonarroti", "Renaissance", "Italie", "Basilique Saint-Pierre de Rome"],
    ["Christopher Wren", "Baroque", "Angleterre", "Cathédrale Saint-Paul de Londres"],
    ["Balthasar Neumann", "Baroque", "Allemagne", "Résidence de Würzburg"],
    ["Charles Garnier", "Éclectisme", "France", "Opéra de Paris"],
    ["Victor Horta", "Art Nouveau", "Belgique", "Hôtel Tassel"],
    ["Walter Gropius", "Modernisme / Bauhaus", "Allemagne", "Bauhaus de Dessau"],
    ["Alvar Aalto", "Modernisme", "Finlande", "Bibliothèque de Viipuri"],
    ["Oscar Niemeyer", "Modernisme", "Brésil", "Parlement de Brasília"],
    ["Louis Kahn", "Modernisme", "États-Unis", "Institut Salk de San Diego"],
    ["Renzo Piano", "Contemporain", "Italie", "Centre Pompidou (avec Rogers)"],
    ["Norman Foster", "High-tech", "Royaume-Uni", "Viaduc de Millau"],
    ["Frank Gehry", "Déconstructivisme", "États-Unis", "Musée Guggenheim de Bilbao"],
    ["Tadao Ando", "Contemporain", "Japon", "Église de la Lumière"],
    ["Jean Nouvel", "Contemporain", "France", "Institut du monde arabe"],
    ["Rem Koolhaas", "Déconstructivisme", "Pays-Bas", "Siège CCTV à Pékin"],
    ["Santiago Calatrava", "Contemporain", "Espagne", "Cité des Arts et des Sciences"],
    ["Herzog & de Meuron", "Contemporain", "Suisse", "Tate Modern de Londres"],
    ["Kengo Kuma", "Contemporain", "Japon", "Stade olympique de Tokyo"],
    ["Dominique Perrault", "Contemporain", "France", "Bibliothèque nationale de France"],
    ["Carlo Scarpa", "Modernisme", "Italie", "Musée de Castelvecchio"],
    ["Richard Rogers", "High-tech", "Royaume-Uni", "Centre Pompidou (avec Piano)"],
    ["Bjarke Ingels", "Contemporain", "Danemark", "8 House de Copenhague"],
]

NEW_MUSEES = [
    ["Musée d’Orsay", "Paris", "France", "Impressionnisme et Art Nouveau"],
    ["Centre Pompidou", "Paris", "France", "Art moderne et contemporain"],
    ["Rijksmuseum", "Amsterdam", "Pays-Bas", "Âge d’or néerlandais"],
    ["Musée Van Gogh", "Amsterdam", "Pays-Bas", "900 tableaux de Van Gogh"],
    ["Kunsthistorisches Museum", "Vienne", "Autriche", "Art des Habsbourg"],
    ["Musée national de Chine", "Pékin", "Chine", "Le plus visité au monde"],
    ["Smithsonian Institution", "Washington", "États-Unis", "19 musées, entrée gratuite"],
    ["Musée de l’Acropole", "Athènes", "Grèce", "Frises du Parthénon"],
    ["Musée égyptien du Caire", "Le Caire", "Égypte", "Trésor de Toutankhamon"],
    ["Museo Nacional de Antropología", "Mexico", "Mexique", "Civilisations mésoaméricaines"],
    ["Tate Modern", "Londres", "Royaume-Uni", "Art du XXe siècle en centrale électrique"],
    ["Musée Guggenheim de Bilbao", "Bilbao", "Espagne", "Architecture déconstructiviste de Gehry"],
    ["Musée du quai Branly", "Paris", "France", "Arts et civilisations non-européens"],
    ["Musée national de Tokyo", "Tokyo", "Japon", "Art et archéologie japonais"],
    ["Musée national de Nairobi", "Nairobi", "Kenya", "Préhistoire humaine et faune africaine"],
    ["Museo del Bargello", "Florence", "Italie", "Sculpture de la Renaissance"],
    ["Musée Rodin", "Paris", "France", "Le Penseur et La Porte de l’Enfer"],
]


def js_str(s: str) -> str:
    """Encode une chaîne Python en littéral JS (guillemets simples, apostrophes Unicode)."""
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def append_to_expansion(html: str, list_id: str, new_items: list[list[str]], anchor_last: str) -> str:
    """Ajoute de nouveaux items à la fin d'un makeExpansionRows([...])."""
    if anchor_last not in html:
        print(f"  ⚠ Ancre non trouvée pour {list_id}, skipped", file=sys.stderr)
        return html

    new_js = "".join(
        f",[{','.join(js_str(v) for v in item)}]"
        for item in new_items
    )
    # Insère les nouveaux items juste après l'ancre (avant la fin du tableau)
    return html.replace(anchor_last, anchor_last + new_js, 1)


def append_to_curated(curated: list, list_id: str, new_rows: list[list[str]]) -> None:
    """Ajoute des lignes à une liste CURATED_LISTS_V3 (en place)."""
    lst = next((l for l in curated if l["id"] == list_id), None)
    if lst is None:
        print(f"  ⚠ Liste {list_id} introuvable dans CURATED", file=sys.stderr)
        return
    start = len(lst["rows"]) + 1
    for i, row_data in enumerate(new_rows):
        n = str(start + i)
        lst["rows"].append([n, f"thumbs/{list_id}/{n}.webp"] + row_data)


def main():
    html = HTML.read_text(encoding="utf-8")

    print("=== Enrichissement EXPANSION_LISTS ===")

    # civilisations — dernière entrée actuelle
    html = append_to_expansion(html, "civilisations",
        NEW_CIVILISATIONS,
        "['Empire inca','XVe–XVIe siècle','Andes','Cuzco et réseau routier']")

    # fleuves_monde
    html = append_to_expansion(html, "fleuves_monde",
        NEW_FLEUVES,
        "['Mékong','4 350 km','Asie','Mer de Chine méridionale']")

    # Fallback : le fichier peut avoir "Mélong" (coquille)
    if "thumbs/fleuves_monde/13.webp" not in html:
        html = append_to_expansion(html, "fleuves_monde",
            NEW_FLEUVES,
            "['Mélong','4 350 km','Asie','Mer de Chine méridionale']")

    # compositeurs
    html = append_to_expansion(html, "compositeurs",
        NEW_COMPOSITEURS,
        "['Igor Stravinsky','XXe siècle','Russe','Le Sacre du printemps']")

    # constellations
    html = append_to_expansion(html, "constellations",
        NEW_CONSTELLATIONS,
        "['Lion','Nord','Régulus','Signe du zodiaque']")

    # grands_scientifiques
    html = append_to_expansion(html, "grands_scientifiques",
        NEW_SCIENTIFIQUES,
        "['Jane Goodall','Primatologie','Britannique','Étude des chimpanzés']")

    print("=== Enrichissement CURATED_LISTS_V3 ===")

    # Extraction du bloc CURATED_LISTS_V3
    m = re.search(r'const CURATED_LISTS_V3 = (\[.*?\]);', html, re.DOTALL)
    if not m:
        print("⚠ CURATED_LISTS_V3 introuvable", file=sys.stderr)
        return

    curated = json.loads(m.group(1))

    append_to_curated(curated, "batailles_decisives", NEW_BATAILLES)
    append_to_curated(curated, "grandes_explorations", NEW_EXPLORATIONS)
    append_to_curated(curated, "montagnes_monde", NEW_MONTAGNES)
    append_to_curated(curated, "detroits_monde", NEW_DETROITS)
    append_to_curated(curated, "parcs_nationaux", NEW_PARCS)
    append_to_curated(curated, "architectes_majeurs", NEW_ARCHITECTES)
    append_to_curated(curated, "musees_monde", NEW_MUSEES)

    new_curated_json = json.dumps(curated, ensure_ascii=False, separators=(",", ":"))
    html = html[:m.start(1)] + new_curated_json + html[m.end(1):]

    HTML.write_text(html, encoding="utf-8")
    print(f"\n✓ {HTML.name} mis à jour")

    # Comptes finaux
    for lst in curated:
        print(f"  {lst['id']}: {len(lst['rows'])} lignes")


if __name__ == "__main__":
    main()
