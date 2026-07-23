"""
Upgrade TOUTES les full/ vers 1200px source / max 1200px JPEG q88.
Ne touche PAS aux thumbs/.
Skips : pays (drapeaux), departements (SVGs).
"""
import sys, pathlib, requests, time, json
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO

BASE    = pathlib.Path(r'C:\Users\flxjr\OneDrive\Bureau\memo-app')
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}
API     = 'https://en.wikipedia.org/w/api.php'
SKIP    = {'pays', 'departements', 'etats_usa', 'elements', 'periodes_geologiques',
           'vocabulaire_precis', 'phrasal_verbs', 'os'}

FAIL_LOG = BASE / 'build' / 'upgrade_full_fails.txt'
OK_LOG   = BASE / 'build' / 'upgrade_full_ok.txt'

def get_url(title, size=1200):
    time.sleep(1.3)
    try:
        r = requests.get(API, params={
            'action': 'query', 'titles': title,
            'prop': 'pageimages', 'pithumbsize': size,
            'format': 'json'
        }, headers=HEADERS, timeout=20)
        for p in r.json().get('query', {}).get('pages', {}).values():
            src = p.get('thumbnail', {}).get('source', '')
            if src and not src.lower().endswith('.svg'):
                return src
    except Exception as e:
        print(f'    API ERR: {e}')
    return None

def save_full(url, folder, num):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        img = Image.open(BytesIO(r.content)).convert('RGB')
        img.thumbnail((1200, 1200), Image.LANCZOS)
        out = BASE / 'full' / folder / f'{num}.jpg'
        img.save(out, 'JPEG', quality=88)
        return out.stat().st_size
    except Exception as e:
        print(f'    SAVE ERR: {e}')
        return 0

def search_term(folder, num, r0, r2, r3):
    """Génère le titre Wikipedia selon la liste."""
    # -- Listes spéciales --
    if folder == 'jo_ete':
        return f'{r2} Summer Olympics'
    if folder == 'jo_hiver':
        return f'{r2} Winter Olympics'
    if folder == 'coupes_monde':
        return f'{r2} FIFA World Cup'
    if folder == 'consoles':
        return r3  # nom de la console
    if folder == 'f1_champions':
        return r3  # nom du pilote
    if folder == 'films':
        return r3  # titre du film
    if folder == 'lunes':
        n = r2.strip()
        return f'{n} (moon)'
    if folder == 'constellations':
        return f'{r2} (constellation)'
    if folder == 'mythologie':
        return f'{r2} (mythology)' if r2 not in ('Zeus','Héra','Poséidon','Athéna','Apollon','Arès','Aphrodite','Hermès','Dionysos','Hadès') else r2
    if folder == 'detroits_monde':
        return f'Strait of {r2}' if r2 not in ('Bosphore','Gibraltar','Dardanelles','Malacca','Béring','Magellan','Pas-de-Calais','Messine','Taïwan','Corée','Lombok','Bass','Floride','Skagerrak','Øresund','Mozambique','Singapour','Bab-el-Mandeb','Ormuz') else r2
    if folder == 'mers_oceans':
        return r2
    if folder == 'fleuves_monde':
        return f'{r2} River' if 'Fleuve' not in r2 else r2
    if folder == 'montagnes_monde':
        return r2
    if folder in ('xixe', 'xxe'):
        return r3.split('(')[0].strip()  # titre événement sans parenthèses
    if folder == 'batailles_decisives':
        return f'Battle of {r2}'
    # -- Par défaut : nom de l'entrée --
    return r2

# ── Charger toutes les données des listes ──
LIST_DATA = {}

# Données hardcodées depuis localStorage (récupérées plus haut)
LIST_DATA['litterature'] = [
    (1,'L\'Iliade','Homère'),(2,'L\'Odyssée','Homère'),(3,'L\'Énéide','Virgile'),
    (4,'Les Métamorphoses','Ovide'),(5,'La Divine Comédie','Dante Alighieri'),
    (6,'Le Décaméron','Giovanni Boccace'),(7,'Don Quichotte','Miguel de Cervantes'),
    (8,'Hamlet','William Shakespeare'),(9,'Roméo et Juliette','William Shakespeare'),
    (10,'Le Roi Lear','William Shakespeare'),(11,'Les Essais','Michel de Montaigne'),
    (12,'Faust','Johann Wolfgang von Goethe'),(13,'Les Misérables','Victor Hugo'),
    (14,'Notre-Dame de Paris','Victor Hugo'),(15,'Le Rouge et le Noir','Stendhal'),
    (16,'La Chartreuse de Parme','Stendhal'),(17,'Le Père Goriot','Honoré de Balzac'),
    (18,'Madame Bovary','Gustave Flaubert'),(19,'Crime et Châtiment','Fiodor Dostoïevski'),
    (20,'Les Frères Karamazov','Fiodor Dostoïevski'),(21,'Guerre et Paix','Léon Tolstoï'),
    (22,'Anna Karénine','Léon Tolstoï'),(23,'Germinal','Émile Zola'),
    (24,'Les Aventures de Huckleberry Finn','Mark Twain'),(25,'Moby Dick','Herman Melville'),
    (26,'Les Hauts de Hurlevent','Emily Brontë'),(27,'Jane Eyre','Charlotte Brontë'),
    (28,'Le Portrait de Dorian Gray','Oscar Wilde'),
    (29,'À la recherche du temps perdu','Marcel Proust'),(30,'Ulysse','James Joyce'),
    (31,'Mrs Dalloway','Virginia Woolf'),(32,'La Montagne magique','Thomas Mann'),
    (33,'L\'Étranger','Albert Camus'),(34,'La Nausée','Jean-Paul Sartre'),
    (35,'Le Procès','Franz Kafka'),(36,'La Métamorphose','Franz Kafka'),
    (37,'1984','George Orwell'),(38,'La Ferme des animaux','George Orwell'),
    (39,'Le Meilleur des mondes','Aldous Huxley'),(40,'Fahrenheit 451','Ray Bradbury'),
    (41,'Le Seigneur des anneaux','J.R.R. Tolkien'),(42,'L\'Attrape-cœurs','J.D. Salinger'),
    (43,'Sur la route','Jack Kerouac'),(44,'Cent ans de solitude','Gabriel García Márquez'),
    (45,'Le Maître et Marguerite','Mikhaïl Boulgakov'),(46,'Lolita','Vladimir Nabokov'),
    (47,'Le Bruit et la Fureur','William Faulkner'),(48,'Beloved','Toni Morrison'),
    (49,'Le Nom de la rose','Umberto Eco'),(50,'Les Raisins de la colère','John Steinbeck'),
    (51,'Les Fleurs du mal','Charles Baudelaire'),(52,'Voyage au bout de la nuit','Louis-Ferdinand Céline'),
    (53,'La Condition humaine','André Malraux'),(54,'Dune','Frank Herbert'),
    (55,'Fondation','Isaac Asimov'),(56,'Le Guide du voyageur galactique','Douglas Adams'),
    (57,'Harry Potter (série)','J.K. Rowling'),(58,'L\'Alchimiste','Paulo Coelho'),
    (59,'L\'Assommoir','Émile Zola'),(60,'Invisible Man','Ralph Ellison'),
]

LIST_DATA['peintres'] = [
    (1,'Jan van Eyck','Primitifs flamands'),(2,'Sandro Botticelli','Quattrocento'),
    (3,'Léonard de Vinci','Haute Renaissance'),(4,'Albrecht Dürer','Renaissance nordique'),
    (5,'Michel-Ange','Haute Renaissance'),(6,'Raphaël','Haute Renaissance'),
    (7,'Titien','Renaissance vénitienne'),(8,"Pieter Bruegel l'Ancien",'Maniérisme flamand'),
    (9,'Le Caravage','Baroque'),(10,'Pierre Paul Rubens','Baroque flamand'),
    (11,'Nicolas Poussin','Classicisme'),(12,'Rembrandt','Siècle d\'or néerlandais'),
    (13,'Jan Vermeer','Siècle d\'or néerlandais'),(14,'Francisco de Goya','Néoclassicisme'),
    (15,'Jacques-Louis David','Néoclassicisme'),(16,'Caspar David Friedrich','Romantisme'),
    (17,'Eugène Delacroix','Romantisme'),(18,'Gustave Courbet','Réalisme'),
    (19,'Édouard Manet','Réalisme'),(20,'Edgar Degas','Impressionnisme'),
    (21,'Paul Cézanne','Post-impressionnisme'),(22,'Claude Monet','Impressionnisme'),
    (23,'Pierre-Auguste Renoir','Impressionnisme'),(24,'Paul Gauguin','Post-impressionnisme'),
    (25,'Vincent van Gogh','Post-impressionnisme'),(26,'Georges Seurat','Pointillisme'),
    (27,'Gustav Klimt','Art nouveau'),(28,'Edvard Munch','Expressionnisme'),
    (29,'Vassily Kandinsky','Expressionnisme abstrait'),(30,'Henri Matisse','Fauvisme'),
    (31,'Paul Klee','Bauhaus'),(32,'Pablo Picasso','Cubisme'),
    (33,'Edward Hopper','Réalisme américain'),(34,'Amedeo Modigliani','École de Paris'),
    (35,'Diego Rivera','Muralisme mexicain'),(36,'Marcel Duchamp','Dadaïsme'),
    (37,'Giorgio de Chirico','Métaphysique'),(38,'Joan Miró','Surréalisme'),
    (39,'Mark Rothko','Expressionnisme abstrait'),(40,'Salvador Dalí','Surréalisme'),
    (41,'Frida Kahlo','Surréalisme'),(42,'Francis Bacon','Expressionnisme figuratif'),
    (43,'Jackson Pollock','Expressionnisme abstrait'),(44,'René Magritte','Surréalisme'),
    (45,'Andy Warhol','Pop Art'),(46,'Jean-Michel Basquiat','Néo-expressionnisme'),
    (47,'Banksy','Street Art'),
]

LIST_DATA['rois_france'] = [
    (1,'Clovis Ier',''),(2,'Clotaire Ier',''),(3,'Chilpéric Ier',''),(4,'Clotaire II',''),
    (5,'Dagobert Ier',''),(6,'Clovis II',''),(7,'Clotaire III',''),(8,'Thierry III',''),
    (9,'Clovis IV',''),(10,'Childebert III',''),(11,'Dagobert III',''),(12,'Chilpéric II',''),
    (13,'Thierry IV',''),(14,'Childéric III',''),(15,'Pépin le Bref',''),(16,'Charlemagne',''),
    (17,'Louis Ier le Pieux',''),(18,'Charles II le Chauve',''),(19,'Louis II le Bègue',''),
    (20,'Louis III',''),(21,'Carloman II',''),(22,'Charles III le Gros',''),
    (23,'Eudes Ier',''),(24,'Charles III le Simple',''),(25,'Robert Ier',''),
    (26,'Raoul',''),(27,"Louis IV d'Outremer",''),(28,'Lothaire',''),(29,'Louis V',''),
    (30,'Hugues Capet',''),(31,'Robert II le Pieux',''),(32,'Henri Ier',''),
    (33,'Philippe Ier',''),(34,'Louis VI le Gros',''),(35,'Louis VII le Jeune',''),
    (36,'Philippe II Auguste',''),(37,'Louis VIII le Lion',''),(38,'Louis IX',''),(39,'Philippe III',''),
    (40,'Philippe IV le Bel',''),(41,'Louis X le Hutin',''),(42,'Jean Ier le Posthume',''),
    (43,'Philippe V le Long',''),(44,'Charles IV le Bel',''),(45,'Philippe VI de Valois',''),
    (46,'Jean II le Bon',''),(47,'Charles V le Sage',''),(48,'Charles VI',''),
    (49,'Charles VII',''),(50,'Louis XI',''),(51,'Charles VIII',''),(52,'Louis XII',''),
    (53,'François Ier',''),(54,'Henri II',''),(55,'François II',''),(56,'Charles IX',''),
    (57,'Henri III',''),(58,'Henri IV',''),(59,'Louis XIII',''),(60,'Louis XIV',''),
    (61,'Louis XV',''),(62,'Louis XVI',''),(63,'Napoléon Ier',''),(64,'Louis XVIII',''),
    (65,'Charles X',''),(66,'Louis-Philippe Ier',''),(67,'Napoléon III',''),
]

LIST_DATA['chefs_etat'] = [
    (1,'Louis XVI',''),(2,'Louis XVI',''),(3,'Committee of Public Safety',''),(4,'French Directory',''),
    (5,'Napoleon Bonaparte',''),(6,'Napoleon I',''),(7,'Louis XVIII',''),(8,'Napoleon I',''),
    (9,'Louis XVIII',''),(10,'Charles X of France',''),(11,'Louis-Philippe I',''),(12,'Louis-Eugène Cavaignac',''),
    (13,'Louis-Napoléon Bonaparte',''),(14,'Napoleon III',''),(15,'Adolphe Thiers',''),(16,'Patrice de MacMahon',''),
    (17,'Jules Grévy',''),(18,'Sadi Carnot',''),(19,'Jean Casimir-Perier',''),(20,'Félix Faure',''),
    (21,'Émile Loubet',''),(22,'Armand Fallières',''),(23,'Raymond Poincaré',''),(24,'Paul Deschanel',''),
    (25,'Alexandre Millerand',''),(26,'Gaston Doumergue',''),(27,'Paul Doumer',''),(28,'Albert Lebrun',''),
    (29,'Philippe Pétain',''),(30,'Charles de Gaulle',''),(31,'Félix Gouin',''),(32,'Georges Bidault',''),
    (33,'Léon Blum',''),(34,'Vincent Auriol',''),(35,'René Coty',''),(36,'Charles de Gaulle',''),
    (37,'Georges Pompidou',''),(38,'Valéry Giscard d\'Estaing',''),(39,'François Mitterrand',''),
    (40,'Jacques Chirac',''),(41,'Nicolas Sarkozy',''),(42,'François Hollande',''),(43,'Emmanuel Macron',''),
]

LIST_DATA['lunes'] = [
    (1,'Moon',''),(2,'Phobos (moon)',''),(3,'Deimos (moon)',''),(4,'Metis (moon)',''),(5,'Adrastea (moon)',''),
    (6,'Amalthea (moon)',''),(7,'Thebe (moon)',''),(8,'Io (moon)',''),(9,'Europa (moon)',''),
    (10,'Ganymede (moon)',''),(11,'Callisto (moon)',''),(12,'Leda (moon)',''),(13,'Himalia (moon)',''),
    (14,'Lysithea (moon)',''),(15,'Elara (moon)',''),(16,'Ananke (moon)',''),(17,'Carme (moon)',''),
    (18,'Pasiphae (moon)',''),(19,'Sinope (moon)',''),(20,'Pan (moon)',''),(21,'Atlas (moon)',''),
    (22,'Prometheus (moon)',''),(23,'Pandora (moon)',''),(24,'Mimas (moon)',''),(25,'Enceladus (moon)',''),
    (26,'Tethys (moon)',''),(27,'Telesto (moon)',''),(28,'Calypso (moon)',''),(29,'Dione (moon)',''),
    (30,'Helene (moon)',''),(31,'Rhea (moon)',''),(32,'Titan (moon)',''),(33,'Hyperion (moon)',''),
    (34,'Iapetus',''),(35,'Phoebe (moon)',''),(36,'Puck (moon)',''),(37,'Miranda (moon)',''),
    (38,'Ariel (moon)',''),(39,'Umbriel (moon)',''),(40,'Titania (moon)',''),(41,'Oberon (moon)',''),
    (42,'Caliban (moon)',''),(43,'Sycorax (moon)',''),(44,'Naiad (moon)',''),(45,'Thalassa (moon)',''),
    (46,'Despina (moon)',''),(47,'Galatea (moon)',''),(48,'Larissa (moon)',''),(49,'Proteus (moon)',''),
    (50,'Triton (moon)',''),(51,'Nereid (moon)',''),(52,'Charon (moon)',''),(53,'Styx (moon)',''),
    (54,'Nix (moon)',''),(55,'Kerberos (moon)',''),(56,'Hydra (moon)',''),
]

LIST_DATA['constellations'] = [
    (1,'Orion (constellation)',''),(2,'Ursa Major',''),(3,'Ursa Minor',''),(4,'Cassiopeia (constellation)',''),
    (5,'Cygnus (constellation)',''),(6,'Lyra',''),(7,'Aquila (constellation)',''),(8,'Scorpius',''),
    (9,'Sagittarius (constellation)',''),(10,'Taurus (constellation)',''),(11,'Gemini (constellation)',''),
    (12,'Leo (constellation)',''),(13,'Perseus (constellation)',''),(14,'Andromeda (constellation)',''),
    (15,'Hercules (constellation)',''),(16,'Virgo (constellation)',''),(17,'Libra (constellation)',''),
    (18,'Aquarius (constellation)',''),(19,'Aries (constellation)',''),(20,'Cancer (constellation)',''),
    (21,'Capricornus',''),(22,'Pisces (constellation)',''),(23,'Centaurus',''),(24,'Crux',''),
    (25,'Draco (constellation)',''),(26,'Pegasus (constellation)',''),(27,'Canis Major',''),
    (28,'Canis Minor',''),(29,'Auriga (constellation)',''),(30,'Boötes',''),(31,'Corona Borealis',''),
    (32,'Ophiuchus',''),(33,'Hydra (constellation)',''),(34,'Eridanus (constellation)',''),
    (35,'Corvus (constellation)',''),(36,'Lepus (constellation)',''),(37,'Phoenix (constellation)',''),
    (38,'Serpens',''),
]

LIST_DATA['mers_oceans'] = [
    (1,'Pacific Ocean',''),(2,'Atlantic Ocean',''),(3,'Indian Ocean',''),(4,'Arctic Ocean',''),
    (5,'Mediterranean Sea',''),(6,'Caribbean Sea',''),(7,'Red Sea',''),(8,'Baltic Sea',''),
    (9,'Southern Ocean',''),(10,'South China Sea',''),(11,'Coral Sea',''),(12,'Tasman Sea',''),
    (13,'Arabian Sea',''),(14,'Sea of Oman',''),(15,'Gulf of Mexico',''),(16,'Persian Gulf',''),
    (17,'North Sea',''),(18,'Black Sea',''),(19,'Caspian Sea',''),(20,'Aegean Sea',''),
]

LIST_DATA['detroits_monde'] = [
    (1,'Strait of Gibraltar',''),(2,'Bosphorus',''),(3,'Dardanelles',''),(4,'Strait of Hormuz',''),
    (5,'Strait of Malacca',''),(6,'Bering Strait',''),(7,'Strait of Magellan',''),
    (8,'Bab-el-Mandeb',''),(9,'Strait of Dover',''),(10,'Strait of Messina',''),
    (11,'Skagerrak',''),(12,'Taiwan Strait',''),(13,'Korea Strait',''),(14,'Lombok Strait',''),
    (15,'Bass Strait',''),(16,'Straits of Florida',''),(17,'Øresund',''),(18,'Mozambique Channel',''),
    (19,'Singapore Strait',''),(20,'Tsugaru Strait',''),
]

LIST_DATA['parcs_nationaux'] = [
    (1,'Yellowstone National Park',''),(2,'Yosemite National Park',''),(3,'Banff National Park',''),
    (4,'Kruger National Park',''),(5,'Serengeti National Park',''),(6,'Torres del Paine National Park',''),
    (7,'Fiordland National Park',''),(8,'Kakadu National Park',''),(9,'Grand Canyon National Park',''),
    (10,'Galápagos National Park',''),(11,'Iguazu National Park',''),(12,'Everglades National Park',''),
    (13,'Great Barrier Reef',''),(14,'Vanoise National Park',''),(15,'Gran Paradiso National Park',''),
    (16,'Virunga National Park',''),(17,'Sagarmatha National Park',''),(18,'Jiuzhaigou',''),(19,'Sundarbans',''),
    (20,'Kaziranga National Park',''),(21,'Denali National Park',''),(22,'Cévennes National Park',''),
    (23,'Pyrenees National Park',''),(24,'Pantanal Conservation Area',''),(25,'Okavango Delta',''),
    (26,'Białowieża Forest',''),(27,'Simien Mountains National Park',''),(28,'Bwindi Impenetrable Forest',''),
    (29,'Wrangell–St. Elias National Park',''),(30,'Dolomites',''),
]

LIST_DATA['architectes_majeurs'] = [
    (1,'Filippo Brunelleschi',''),(2,'Andrea Palladio',''),(3,'Antoni Gaudí',''),(4,'Frank Lloyd Wright',''),
    (5,'Le Corbusier',''),(6,'Ludwig Mies van der Rohe',''),(7,'Zaha Hadid',''),(8,'I. M. Pei',''),
    (9,'Michelangelo',''),(10,'Christopher Wren',''),(11,'Balthasar Neumann',''),(12,'Charles Garnier',''),
    (13,'Victor Horta',''),(14,'Walter Gropius',''),(15,'Alvar Aalto',''),(16,'Oscar Niemeyer',''),
    (17,'Louis Kahn',''),(18,'Renzo Piano',''),(19,'Norman Foster',''),(20,'Frank Gehry',''),
    (21,'Tadao Ando',''),(22,'Jean Nouvel',''),(23,'Rem Koolhaas',''),(24,'Santiago Calatrava',''),
    (25,'Herzog & de Meuron',''),(26,'Kengo Kuma',''),(27,'Dominique Perrault',''),(28,'Carlo Scarpa',''),
    (29,'Richard Rogers',''),(30,'Bjarke Ingels',''),
]

LIST_DATA['musees_monde'] = [
    (1,'Louvre Museum',''),(2,'Metropolitan Museum of Art',''),(3,'Museo del Prado',''),(4,'British Museum',''),
    (5,'Vatican Museums',''),(6,'Uffizi Gallery',''),(7,'Museum of Modern Art',''),(8,'Hermitage Museum',''),
    (9,'Musée d\'Orsay',''),(10,'Centre Pompidou',''),(11,'Rijksmuseum',''),(12,'Van Gogh Museum',''),
    (13,'Kunsthistorisches Museum',''),(14,'National Museum of China',''),(15,'Smithsonian Institution',''),
    (16,'Acropolis Museum',''),(17,'Egyptian Museum (Cairo)',''),(18,'National Museum of Anthropology (Mexico City)',''),
    (19,'Tate Modern',''),(20,'Guggenheim Museum Bilbao',''),(21,'Musée du quai Branly',''),
    (22,'Tokyo National Museum',''),(23,'National Museums of Kenya',''),(24,'Bargello',''),(25,'Musée Rodin',''),
]

LIST_DATA['mouvements_peinture'] = [
    (1,'Cave painting',''),(2,'Ancient Egyptian art',''),(3,'Ancient Greek art',''),(4,'Roman art',''),
    (5,'Byzantine art',''),(6,'Romanesque art',''),(7,'Gothic art',''),(8,'Early Netherlandish painting',''),
    (9,'Quattrocento',''),(10,'High Renaissance',''),(11,'Mannerism',''),(12,'Northern Renaissance',''),
    (13,'Baroque',''),(14,'French classicism',''),(15,'Rococo',''),(16,'Neoclassicism',''),
    (17,'Romanticism',''),(18,'Realism (art movement)',''),(19,'Pre-Raphaelite Brotherhood',''),
    (20,'Impressionism',''),(21,'Post-Impressionism',''),(22,'Pointillism',''),(23,'Symbolism (arts)',''),
    (24,'Art Nouveau',''),(25,'Fauvism',''),(26,'Expressionism',''),(27,'Cubism',''),(28,'Futurism',''),
    (29,'Dada',''),(30,'Constructivism (art)',''),(31,'De Stijl',''),(32,'Bauhaus',''),
    (33,'Surrealism',''),(34,'Abstract expressionism',''),(35,'Pop art',''),(36,'Minimalism',''),
    (37,'Conceptual art',''),(38,'Hyperrealism (painting)',''),(39,'Neo-expressionism',''),
    (40,'Street art',''),(41,'Digital art',''),
]

LIST_DATA['decouvertes_scientifiques'] = [
    (1,'Heliocentrism',''),(2,'Kepler\'s laws of planetary motion',''),(3,'Circulation of blood',''),
    (4,'Calculus',''),(5,'Newton\'s law of universal gravitation',''),(6,'Lightning rod',''),
    (7,'Oxygen',''),(8,'Laws of thermodynamics',''),(9,'Natural selection',''),(10,'Electromagnetic radiation',''),
    (11,'Periodic table',''),(12,'X-ray',''),(13,'Radioactivity',''),(14,'Special relativity',''),
    (15,'Plate tectonics',''),(16,'Quantum mechanics',''),(17,'Penicillin',''),(18,'Nuclear fission',''),
    (19,'DNA',''),(20,'Cosmic microwave background radiation',''),(21,'Quark',''),(22,'Exoplanet',''),
    (23,'Higgs boson',''),(24,'Gravitational wave',''),
]

LIST_DATA['batailles_decisives'] = [
    (1,'Battle of Marathon',''),(2,'Battle of Hastings',''),(3,'Battle of Bouvines',''),(4,'Battle of Waterloo',''),
    (5,'Battle of Verdun',''),(6,'Battle of Stalingrad',''),(7,'Battle of Midway',''),
    (8,'Battle of Dien Bien Phu',''),(9,'Battle of Gaugamela',''),(10,'Battle of Cannae',''),
    (11,'Battle of Actium',''),(12,'Battle of the Catalaunian Plains',''),(13,'Battle of Yarmouk',''),
    (14,'Battle of Tours',''),(15,'Battle of Lepanto',''),(16,'Battle of Rocroi',''),(17,'Battle of Poltava',''),
    (18,'Battle of Plassey',''),(19,'Siege of Yorktown (1781)',''),(20,'Battle of Valmy',''),
    (21,'Battle of Austerlitz',''),(22,'Battle of Leipzig',''),(23,'Battle of Tsushima',''),
    (24,'Battle of the Marne (1914)',''),(25,'Battle of the Somme',''),(26,'Second Battle of El Alamein',''),
    (27,'Battle of Kursk',''),(28,'Normandy landings',''),(29,'Battle of Berlin (1945)',''),
    (30,'Battle of Inchon',''),(31,'Yom Kippur War',''),(32,'Falklands War',''),(33,'Gulf War',''),
]

LIST_DATA['compositeurs'] = [
    (1,'Johann Sebastian Bach',''),(2,'Antonio Vivaldi',''),(3,'George Frideric Handel',''),
    (4,'Joseph Haydn',''),(5,'Wolfgang Amadeus Mozart',''),(6,'Ludwig van Beethoven',''),
    (7,'Franz Schubert',''),(8,'Frédéric Chopin',''),(9,'Giuseppe Verdi',''),(10,'Richard Wagner',''),
    (11,'Claude Debussy',''),(12,'Igor Stravinsky',''),(13,'Johannes Brahms',''),(14,'Hector Berlioz',''),
    (15,'Pyotr Ilyich Tchaikovsky',''),(16,'Gustav Mahler',''),(17,'Giacomo Puccini',''),
    (18,'Franz Liszt',''),(19,'Robert Schumann',''),(20,'Sergei Rachmaninoff',''),(21,'Dmitri Shostakovich',''),
    (22,'Béla Bartók',''),(23,'Leonard Bernstein',''),(24,'Maurice Ravel',''),(25,'Gabriel Fauré',''),
    (26,'Camille Saint-Saëns',''),(27,'Claudio Monteverdi',''),(28,'Edvard Grieg',''),(29,'Jean Sibelius',''),
    (30,'Antonín Dvořák',''),(31,'Sergei Prokofiev',''),(32,'Aaron Copland',''),(33,'Benjamin Britten',''),
    (34,'Philip Glass',''),(35,'Georges Bizet',''),(36,'Henry Purcell',''),(37,'Christoph Willibald Gluck',''),
    (38,'Carl Maria von Weber',''),(39,'Jean-Philippe Rameau',''),
]

LIST_DATA['mythologie'] = [
    (1,'Zeus',''),(2,'Hera',''),(3,'Poseidon',''),(4,'Demeter',''),(5,'Athena (mythology)',''),
    (6,'Apollo (mythology)',''),(7,'Artemis',''),(8,'Ares',''),(9,'Aphrodite',''),(10,'Hephaestus',''),
    (11,'Hermes (mythology)',''),(12,'Dionysus',''),(13,'Hades',''),(14,'Persephone',''),(15,'Hestia',''),
    (16,'Nyx',''),(17,'Chaos (cosmogony)',''),(18,'Cronus',''),(19,'Hecate',''),(20,'Thanatos',''),
    (21,'Hypnos',''),(22,'Charon (mythology)',''),(23,'Eros',''),(24,'Nike (mythology)',''),
    (25,'Prometheus',''),(26,'Atlas (mythology)',''),(27,'Zagreus',''),(28,'Melinoe',''),
    (29,'Megaera',''),(30,'Alecto',''),(31,'Tisiphone',''),(32,'Heracles',''),
    (33,'Achilles',''),(34,'Odysseus',''),(35,'Theseus',''),(36,'Minotaur',''),(37,'Orpheus',''),
    (38,'Eurydice (mythology)',''),(39,'Sisyphus',''),(40,'Perseus',''),(41,'Medusa',''),
    (42,'Icarus',''),(43,'Daedalus',''),(44,'Narcissus (mythology)',''),(45,'Echo (mythology)',''),
    (46,'Arachne',''),(47,'Oedipus',''),(48,'Pandora',''),(49,'Eris (mythology)',''),
    (50,'Helios',''),(51,'Selene',''),(52,'Tyche',''),(53,'Aeolus',''),(54,'Cerberus',''),
    (55,'Medea',''),(56,'Moros',''),(57,'Tantalus',''),(58,'Ixion',''),(59,'Hyperion (mythology)',''),
]

LIST_DATA['philosophes'] = [
    (1,'Socrates',''),(2,'Plato',''),(3,'Aristotle',''),(4,'Epicurus',''),(5,'Zeno of Citium',''),
    (6,'Marcus Aurelius',''),(7,'Epictetus',''),(8,'Augustine of Hippo',''),(9,'Thomas Aquinas',''),
    (10,'Niccolò Machiavelli',''),(11,'Francis Bacon',''),(12,'Thomas Hobbes',''),(13,'René Descartes',''),
    (14,'Blaise Pascal',''),(15,'John Locke',''),(16,'Baruch Spinoza',''),(17,'Gottfried Wilhelm Leibniz',''),
    (18,'Montesquieu',''),(19,'Voltaire',''),(20,'David Hume',''),(21,'Jean-Jacques Rousseau',''),
    (22,'Adam Smith',''),(23,'Immanuel Kant',''),(24,'Georg Wilhelm Friedrich Hegel',''),
    (25,'Arthur Schopenhauer',''),(26,'Auguste Comte',''),(27,'John Stuart Mill',''),(28,'Karl Marx',''),
    (29,'Friedrich Nietzsche',''),(30,'Edmund Husserl',''),(31,'Henri Bergson',''),
    (32,'Bertrand Russell',''),(33,'Ludwig Wittgenstein',''),(34,'Martin Heidegger',''),
    (35,'Hannah Arendt',''),(36,'Jean-Paul Sartre',''),(37,'Simone de Beauvoir',''),
    (38,'Albert Camus',''),(39,'Claude Lévi-Strauss',''),(40,'Michel Foucault',''),
    (41,'Gilles Deleuze',''),(42,'Jacques Derrida',''),(43,'John Rawls',''),(44,'Jürgen Habermas',''),
    (45,'Peter Singer',''),
]

LIST_DATA['grandes_explorations'] = [
    (1,'Zheng He',''),(2,'Christopher Columbus',''),(3,'Vasco da Gama',''),
    (4,'Ferdinand Magellan',''),(5,'James Cook',''),(6,'Alexander von Humboldt',''),
    (7,'David Livingstone',''),(8,'Roald Amundsen',''),(9,'Ibn Battuta',''),
    (10,'Bartolomeu Dias',''),(11,'Amerigo Vespucci',''),(12,'Hernán Cortés',''),
    (13,'Francisco Pizarro',''),(14,'Jacques Cartier',''),(15,'Francis Drake',''),
    (16,'Samuel de Champlain',''),(17,'Abel Tasman',''),(18,'Mungo Park (explorer)',''),
    (19,'Lewis and Clark Expedition',''),(20,'René Caillié',''),(21,'Ernest Shackleton',''),
    (22,'Edmund Hillary',''),(23,'Jacques Piccard',''),(24,'Neil Armstrong',''),
    (25,'Valentina Tereshkova',''),
]

LIST_DATA['grands_scientifiques'] = [
    (1,'Archimedes',''),(2,'Ibn al-Haytham',''),(3,'Nicolaus Copernicus',''),(4,'Galileo Galilei',''),
    (5,'Isaac Newton',''),(6,'Antoine Lavoisier',''),(7,'Charles Darwin',''),(8,'Marie Curie',''),
    (9,'Albert Einstein',''),(10,'Rosalind Franklin',''),(11,'Katherine Johnson',''),
    (12,'Jane Goodall',''),(13,'Euclid',''),(14,'Hippocrates',''),(15,'Leonardo da Vinci',''),
    (16,'Johannes Kepler',''),(17,'Christiaan Huygens',''),(18,'Carl Linnaeus',''),
    (19,'Alessandro Volta',''),(20,'Michael Faraday',''),(21,'James Clerk Maxwell',''),
    (22,'Louis Pasteur',''),(23,'Gregor Mendel',''),(24,'Nikola Tesla',''),(25,'Max Planck',''),
    (26,'Niels Bohr',''),(27,'Lise Meitner',''),(28,'Alan Turing',''),(29,'Barbara McClintock',''),
    (30,'Carl Sagan',''),(31,'Stephen Hawking',''),(32,'Tim Berners-Lee',''),(33,'Tycho Brahe',''),
    (34,'Robert Hooke',''),(35,'Dmitri Mendeleev',''),(36,'Werner Heisenberg',''),
    (37,'Francis Crick',''),(38,'James Watson',''),
]

LIST_DATA['inventions_majeures'] = [
    (1,'Wheel',''),(2,'Cuneiform',''),(3,'Glasses (vision correction)',''),(4,'Printing press',''),
    (5,'Movable type',''),(6,'Thermometer',''),(7,'Telescope',''),(8,'Mechanical calculator',''),
    (9,'Steam engine',''),(10,'Vaccine',''),(11,'Steam locomotive',''),(12,'Photography',''),
    (13,'Dynamo',''),(14,'Electrical telegraph',''),(15,'Anesthesia',''),(16,'Telephone',''),
    (17,'Internal combustion engine',''),(18,'Incandescent light bulb',''),(19,'Radio',''),(20,'Film',''),
    (21,'Fixed-wing aircraft',''),(22,'Penicillin',''),(23,'Radar',''),(24,'Stored-program computer',''),
    (25,'Transistor',''),(26,'Sputnik 1',''),(27,'Laser',''),(28,'ARPANET',''),(29,'World Wide Web',''),
    (30,'Compass',''),(31,'Gunpowder',''),
]

LIST_DATA['civilisations'] = [
    (1,'Mesopotamia',''),(2,'Ancient Egypt',''),(3,'Indus Valley Civilisation',''),(4,'Shang dynasty',''),
    (5,'Ancient Greece',''),(6,'Ancient Rome',''),(7,'Byzantine Empire',''),(8,'Kingdom of Aksum',''),
    (9,'Mali Empire',''),(10,'Maya civilization',''),(11,'Aztec Empire',''),(12,'Inca Empire',''),
    (13,'Carthage',''),(14,'Achaemenid Empire',''),(15,'Maurya Empire',''),(16,'Han dynasty',''),
    (17,'Sasanian Empire',''),(18,'Gupta Empire',''),(19,'Abbasid Caliphate',''),(20,'Mongol Empire',''),
    (21,'Ottoman Empire',''),(22,'Teotihuacan',''),(23,'Nubia',''),(24,'Songhai Empire',''),
    (25,'Mughal Empire',''),(26,'Feudal Japan',''),(27,'British Empire',''),(28,'Soviet Union',''),
]

LIST_DATA['guerres'] = [
    (1,'Greco-Persian Wars',''),(2,'Peloponnesian War',''),(3,'Wars of Alexander the Great',''),
    (4,'Punic Wars',''),(5,'Crusades',''),(6,'Mongol conquests',''),(7,'Hundred Years\' War',''),
    (8,'French Wars of Religion',''),(9,'Thirty Years\' War',''),(10,'Seven Years\' War',''),
    (11,'American Revolutionary War',''),(12,'Napoleonic Wars',''),(13,'Crimean War',''),
    (14,'American Civil War',''),(15,'Franco-Prussian War',''),(16,'War of the Pacific (1879–84)',''),
    (17,'Russo-Japanese War',''),(18,'Balkan Wars',''),(19,'World War I',''),(20,'Russian Civil War',''),
    (21,'Irish War of Independence',''),(22,'Spanish Civil War',''),(23,'World War II',''),
    (24,'First Indochina War',''),(25,'Korean War',''),(26,'Algerian War',''),(27,'Vietnam War',''),
    (28,'Six-Day War',''),(29,'Yom Kippur War',''),(30,'Lebanese Civil War',''),
    (31,'Iran–Iraq War',''),(32,'Falklands War',''),(33,'Gulf War',''),(34,'Bosnian War',''),
    (35,'Kosovo War',''),(36,'War in Afghanistan (2001–2021)',''),(37,'Iraq War',''),
    (38,'Syrian civil war',''),(39,'Yemeni civil war (2014–present)',''),(40,'Russo-Ukrainian War',''),
]

LIST_DATA['jo_ete'] = [
    (1,'1896','Athens'),(2,'1900','Paris'),(3,'1904','St. Louis'),(4,'1906','Athens'),
    (5,'1908','London'),(6,'1912','Stockholm'),(7,'1920','Antwerp'),(8,'1924','Paris'),
    (9,'1928','Amsterdam'),(10,'1932','Los Angeles'),(11,'1936','Berlin'),(12,'1948','London'),
    (13,'1952','Helsinki'),(14,'1956','Melbourne'),(15,'1960','Rome'),(16,'1964','Tokyo'),
    (17,'1968','Mexico City'),(18,'1972','Munich'),(19,'1976','Montreal'),(20,'1980','Moscow'),
    (21,'1984','Los Angeles'),(22,'1988','Seoul'),(23,'1992','Barcelona'),(24,'1996','Atlanta'),
    (25,'2000','Sydney'),(26,'2004','Athens'),(27,'2008','Beijing'),(28,'2012','London'),
    (29,'2016','Rio de Janeiro'),(30,'2020','Tokyo'),(31,'2024','Paris'),(32,'2028','Los Angeles'),
]

LIST_DATA['jo_hiver'] = [
    (1,'1924','Chamonix'),(2,'1928','St. Moritz'),(3,'1932','Lake Placid'),
    (4,'1936','Garmisch-Partenkirchen'),(5,'1948','St. Moritz'),(6,'1952','Oslo'),
    (7,'1956','Cortina d\'Ampezzo'),(8,'1960','Squaw Valley'),(9,'1964','Innsbruck'),
    (10,'1968','Grenoble'),(11,'1972','Sapporo'),(12,'1976','Innsbruck'),(13,'1980','Lake Placid'),
    (14,'1984','Sarajevo'),(15,'1988','Calgary'),(16,'1992','Albertville'),(17,'1994','Lillehammer'),
    (18,'1998','Nagano'),(19,'2002','Salt Lake City'),(20,'2006','Turin'),(21,'2010','Vancouver'),
    (22,'2014','Sochi'),(23,'2018','Pyeongchang'),(24,'2022','Beijing'),(25,'2026','Milan'),
]

LIST_DATA['coupes_monde'] = [
    (1,'1930','Uruguay'),(2,'1934','Italy'),(3,'1938','France'),(4,'1950','Brazil'),
    (5,'1954','Switzerland'),(6,'1958','Sweden'),(7,'1962','Chile'),(8,'1966','England'),
    (9,'1970','Mexico'),(10,'1974','West Germany'),(11,'1978','Argentina'),(12,'1982','Spain'),
    (13,'1986','Mexico'),(14,'1990','Italy'),(15,'1994','United States'),(16,'1998','France'),
    (17,'2002','Japan and South Korea'),(18,'2006','Germany'),(19,'2010','South Africa'),
    (20,'2014','Brazil'),(21,'2018','Russia'),(22,'2022','Qatar'),(23,'2026','USA/Canada/Mexico'),
]

LIST_DATA['consoles'] = [
    (1,'1972','Magnavox Odyssey'),(2,'1975','Pong'),(3,'1977','Atari 2600'),(4,'1977','Fairchild Channel F'),
    (5,'1978','Magnavox Odyssey 2'),(6,'1979','Intellivision'),(7,'1982','ColecoVision'),(8,'1982','Atari 5200'),
    (9,'1983','Nintendo Entertainment System'),(10,'1983','SG-1000'),(11,'1985','Nintendo Entertainment System'),
    (12,'1986','Sega Master System'),(13,'1987','TurboGrafx-16'),(14,'1988','Sega Genesis'),
    (15,'1989','Game Boy'),(16,'1990','Super Nintendo Entertainment System'),(17,'1991','Sega Genesis'),
    (18,'1993','3DO Interactive Multiplayer'),(19,'1994','Sega Saturn'),(20,'1994','PlayStation (console)'),
    (21,'1996','Nintendo 64'),(22,'1996','Game Boy Pocket'),(23,'1998','Game Boy Color'),(24,'1998','Dreamcast'),
    (25,'2000','PlayStation 2'),(26,'2001','Game Boy Advance'),(27,'2001','GameCube'),(28,'2001','Xbox (console)'),
    (29,'2004','Nintendo DS'),(30,'2004','PlayStation Portable'),(31,'2005','Xbox 360'),(32,'2006','PlayStation 3'),
    (33,'2006','Wii'),(34,'2011','Nintendo 3DS'),(35,'2011','PlayStation Vita'),(36,'2012','Wii U'),
    (37,'2013','PlayStation 4'),(38,'2013','Xbox One'),(39,'2017','Nintendo Switch'),(40,'2020','PlayStation 5'),
    (41,'2020','Xbox Series X and Series S'),(42,'2022','Steam Deck'),(43,'2024','Xbox Series S'),
]

LIST_DATA['revolutions'] = [
    (1,'English Civil War',''),(2,'Glorious Revolution',''),(3,'American Revolution',''),
    (4,'French Revolution',''),(5,'Haitian Revolution',''),(6,'Thermidorian Reaction',''),
    (7,'Spanish American wars of independence',''),(8,'Argentine War of Independence',''),
    (9,'Brazilian Independence',''),(10,'French Revolution of 1830',''),(11,'Revolutions of 1848',''),
    (12,'Indian Rebellion of 1857',''),(13,'Paris Commune',''),(14,'Mexican Revolution',''),
    (15,'Xinhai Revolution',''),(16,'Russian Revolution',''),(17,'Turkish War of Independence',''),
    (18,'Second Spanish Republic',''),(19,'Indian independence movement',''),(20,'Cuban Revolution',''),
    (21,'Algerian War',''),(22,'African independence movements',''),(23,'Carnation Revolution',''),
    (24,'Iranian Revolution',''),(25,'Nicaraguan Revolution',''),(26,'Velvet Revolution',''),
    (27,'Fall of the Berlin Wall',''),(28,'Bolivarian Revolution',''),(29,'Arab Spring',''),
    (30,'2014 Ukrainian revolution',''),
]

LIST_DATA['philosophes_skip'] = []  # already in philosophes

LIST_DATA['f1_champions'] = [
    (1,'1950','Giuseppe Farina'),(2,'1951','Juan Manuel Fangio'),(3,'1952','Alberto Ascari'),
    (4,'1953','Alberto Ascari'),(5,'1954','Juan Manuel Fangio'),(6,'1955','Juan Manuel Fangio'),
    (7,'1956','Juan Manuel Fangio'),(8,'1957','Juan Manuel Fangio'),(9,'1958','Mike Hawthorn'),
    (10,'1959','Jack Brabham'),(11,'1960','Jack Brabham'),(12,'1961','Phil Hill'),
    (13,'1962','Graham Hill'),(14,'1963','Jim Clark'),(15,'1964','John Surtees'),
    (16,'1965','Jim Clark'),(17,'1966','Jack Brabham'),(18,'1967','Denny Hulme'),
    (19,'1968','Graham Hill'),(20,'1969','Jackie Stewart'),(21,'1970','Jochen Rindt'),
    (22,'1971','Jackie Stewart'),(23,'1972','Emerson Fittipaldi'),(24,'1973','Jackie Stewart'),
    (25,'1974','Emerson Fittipaldi'),(26,'1975','Niki Lauda'),(27,'1976','James Hunt'),
    (28,'1977','Niki Lauda'),(29,'1978','Mario Andretti'),(30,'1979','Jody Scheckter'),
    (31,'1980','Alan Jones (racing driver)'),(32,'1981','Nelson Piquet'),(33,'1982','Keke Rosberg'),
    (34,'1983','Nelson Piquet'),(35,'1984','Niki Lauda'),(36,'1985','Alain Prost'),
    (37,'1986','Alain Prost'),(38,'1987','Nelson Piquet'),(39,'1988','Ayrton Senna'),
    (40,'1989','Alain Prost'),(41,'1990','Ayrton Senna'),(42,'1991','Ayrton Senna'),
    (43,'1992','Nigel Mansell'),(44,'1993','Alain Prost'),(45,'1994','Michael Schumacher'),
    (46,'1995','Michael Schumacher'),(47,'1996','Damon Hill'),(48,'1997','Jacques Villeneuve'),
    (49,'1998','Mika Häkkinen'),(50,'1999','Mika Häkkinen'),(51,'2000','Michael Schumacher'),
    (52,'2001','Michael Schumacher'),(53,'2002','Michael Schumacher'),(54,'2003','Michael Schumacher'),
    (55,'2004','Michael Schumacher'),(56,'2005','Fernando Alonso'),(57,'2006','Fernando Alonso'),
    (58,'2007','Kimi Räikkönen'),(59,'2008','Lewis Hamilton'),(60,'2009','Jenson Button'),
    (61,'2010','Sebastian Vettel'),(62,'2011','Sebastian Vettel'),(63,'2012','Sebastian Vettel'),
    (64,'2013','Sebastian Vettel'),(65,'2014','Lewis Hamilton'),(66,'2015','Lewis Hamilton'),
    (67,'2016','Nico Rosberg'),(68,'2017','Lewis Hamilton'),(69,'2018','Lewis Hamilton'),
    (70,'2019','Lewis Hamilton'),(71,'2020','Lewis Hamilton'),(72,'2021','Max Verstappen'),
    (73,'2022','Max Verstappen'),(74,'2023','Max Verstappen'),(75,'2024','Max Verstappen'),
    (76,'2025','Lando Norris'),
]

LIST_DATA['fleuves_monde'] = [
    (1,'Nile',''),(2,'Amazon River',''),(3,'Yangtze River',''),(4,'Missouri–Mississippi River System',''),
    (5,'Yenisei',''),(6,'Yellow River',''),(7,'Ob River',''),(8,'Paraná River',''),(9,'Congo River',''),
    (10,'Amur River',''),(11,'Lena River',''),(12,'Mekong',''),(13,'Niger River',''),(14,'Mackenzie River',''),
    (15,'Volga',''),(16,'Zambezi',''),(17,'Orinoco',''),(18,'Euphrates',''),(19,'Tigris',''),
    (20,'Ganges',''),(21,'Indus River',''),(22,'Murray River',''),(23,'Danube',''),(24,'Saint Lawrence River',''),
    (25,'Colorado River',''),(26,'Rio Grande',''),(27,'Orange River',''),(28,'Rhine',''),(29,'Senegal River',''),
    (30,'Irrawaddy River',''),
]

LIST_DATA['montagnes_monde'] = [
    (1,'Mount Everest',''),(2,'K2',''),(3,'Kangchenjunga',''),(4,'Lhotse',''),(5,'Makalu',''),
    (6,'Cho Oyu',''),(7,'Dhaulagiri',''),(8,'Manaslu',''),(9,'Nanga Parbat',''),(10,'Annapurna',''),
    (11,'Aconcagua',''),(12,'Ojos del Salado',''),(13,'Denali',''),(14,'Mount Logan',''),
    (15,'Mount Kilimanjaro',''),(16,'Mount Elbrus',''),(17,'Popocatépetl',''),(18,'Vinson Massif',''),
    (19,'Puncak Jaya',''),(20,'Mont Blanc',''),(21,'Matterhorn',''),(22,'Grand Teton',''),
    (23,'Mount Fuji',''),(24,'Teide',''),(25,'Aneto',''),(26,'Mount Olympus',''),(27,'Mount St. Helens',''),
    (28,'Ben Nevis',''),(29,'Mount Vesuvius',''),(30,'Table Mountain',''),
]

LIST_DATA['films'] = [
    # Titres connus Wikipedia (r[3] = film title)
]
# Films: on utilise le titre du film directement
_films_raw = [(1,'La Sortie de l\'usine Lumière à Lyon'),(2,'L\'Arrivée d\'un train en gare de La Ciotat'),
    (3,'Le Repas de bébé'),(4,'Le Manoir du diable'),(5,'L\'Arroseur arrosé'),
    (22,'A Trip to the Moon'),(25,'The Great Train Robbery'),(76,'The Cabinet of Dr. Caligari'),
    (79,'The Kid (1921 film)'),(81,'Nosferatu'),(91,'The Gold Rush'),(92,'Battleship Potemkin'),
    (97,'Metropolis (1927 film)'),(98,'The Jazz Singer (1927 film)'),(99,'Sunrise: A Song of Two Humans'),
    (100,'The Passion of Joan of Arc'),(104,'Un Chien Andalou'),(109,'M (1931 film)'),(115,'King Kong (1933 film)'),
    (124,'Modern Times (film)'),(127,'La Grande Illusion'),(128,'Snow White and the Seven Dwarfs'),
    (133,'Gone with the Wind (film)'),(134,'The Wizard of Oz (1939 film)'),(136,'The Great Dictator'),
    (139,'Citizen Kane'),(142,'Casablanca (film)'),(148,'Double Indemnity (film)'),
    (151,'Les Enfants du paradis'),(152,'Rome, Open City'),(154,'Beauty and the Beast (1946 film)'),
    (155,"It's a Wonderful Life"),(160,'Bicycle Thieves'),(163,'The Third Man (film)'),
    (166,'Rashomon'),(167,'Sunset Boulevard (film)'),(173,'Singin\' in the Rain'),
    (174,'High Noon (film)'),(175,'Tokyo Story'),(178,'Seven Samurai'),(179,'La Strada (film)'),
    (180,'Rear Window'),(184,'The Seventh Seal'),(187,'Wild Strawberries (film)'),
    (188,'Paths of Glory'),(189,'The Bridge on the River Kwai'),(190,'Vertigo (film)'),
    (193,'The 400 Blows'),(194,'Breathless (1960 film)'),(195,'Ben-Hur (1959 film)'),
    (196,'La Dolce Vita'),(197,'Psycho (1960 film)'),(199,'Jules and Jim'),(201,'West Side Story (1961 film)'),
    (202,'Lawrence of Arabia (film)'),(205,'The Leopard (film)'),(206,'8½'),
    (208,'Dr. Strangelove'),(211,'Doctor Zhivago (film)'),(214,'Au hasard Balthazar'),
    (215,'The Good, the Bad and the Ugly'),(217,'Belle de Jour (film)'),(218,'The Graduate (film)'),
    (219,'Bonnie and Clyde (film)'),(220,'2001: A Space Odyssey (film)'),(222,'Once Upon a Time in the West'),
    (223,'Easy Rider'),(224,'Midnight Cowboy'),(229,'A Clockwork Orange (film)'),
    (232,'The Godfather'),(234,'Cabaret (1972 film)'),(236,'The Exorcist (film)'),
    (238,'Chinatown (1974 film)'),(239,'The Godfather Part II'),(241,'Jaws (film)'),
    (242,'One Flew Over the Cuckoo\'s Nest (film)'),(244,'Taxi Driver'),(247,'Annie Hall'),
    (248,'Star Wars'),(252,'The Deer Hunter'),(253,'Apocalypse Now'),(254,'Alien (film)'),
    (256,'Raging Bull'),(257,'The Shining (film)'),(263,'Blade Runner'),(265,'Fanny and Alexander'),
    (268,'Paris, Texas (film)'),(270,'Amadeus (film)'),(272,'Ran (film)'),(274,'Platoon (film)'),
    (275,'Blue Velvet (film)'),(277,'Full Metal Jacket'),(279,'The Last Emperor'),
    (280,'Rain Man'),(282,'Die Hard'),(286,'Goodfellas'),(288,'Dances with Wolves'),
    (289,'The Silence of the Lambs (film)'),(290,'Terminator 2: Judgment Day'),
    (292,'Unforgiven (1992 film)'),(294,'Reservoir Dogs'),(295,'Schindler\'s List'),
    (298,'Pulp Fiction'),(299,'The Shawshank Redemption'),(300,'Forrest Gump'),(304,'Fargo (1996 film)'),
    (307,'Titanic (1997 film)'),(308,'L.A. Confidential (film)'),(310,'Saving Private Ryan'),
    (311,'Life Is Beautiful'),(312,'The Truman Show'),(313,'American Beauty (film)'),
    (314,'Fight Club (film)'),(316,'Gladiator (2000 film)'),(317,'Requiem for a Dream'),
    (319,'The Lord of the Rings: The Fellowship of the Ring'),(320,'Mulholland Drive (film)'),
    (321,'Memento (film)'),(322,'The Pianist (film)'),(323,'City of God (film)'),
    (325,'Lost in Translation (film)'),(328,'Eternal Sunshine of the Spotless Mind'),
    (330,'Million Dollar Baby'),(331,'Brokeback Mountain'),(334,'Pan\'s Labyrinth'),
    (336,'The Departed (film)'),(337,'No Country for Old Men (film)'),(338,'There Will Be Blood (film)'),
    (340,'The Dark Knight (film)'),(343,'The Hurt Locker'),(346,'Inception (film)'),
    (347,'The Social Network (film)'),(349,'The Artist (film)'),(351,'The Tree of Life (film)'),
    (352,'Amour (2012 film)'),(353,'Django Unchained'),(355,'12 Years a Slave (film)'),
    (356,'Her (film)'),(358,'Boyhood (film)'),(359,'Birdman (film)'),(360,'Whiplash (film)'),
    (361,'Mad Max: Fury Road'),(363,'The Revenant (2015 film)'),(364,'Moonlight (film)'),
    (365,'La La Land (film)'),(367,'Get Out (film)'),(370,'Roma (2018 film)'),
    (373,'Parasite (2019 film)'),(374,'Once Upon a Time in Hollywood'),(375,'Joker (2019 film)'),
    (376,'Nomadland (film)'),(379,'Drive My Car (film)'),(382,'Everything Everywhere All at Once'),
    (385,'Oppenheimer (film)'),(386,'Anatomy of a Fall'),(388,'Anora (film)'),
    (389,'The Brutalist (film)'),
]
LIST_DATA['films'] = [(n, t, '') for n, t in _films_raw]

# ── Fonctions ──
def do_search_term(folder, entry):
    num, r2, r3 = entry
    return search_term(folder, num, str(num), r2, r3)

def process_folder(folder, entries):
    full_dir = BASE / 'full' / folder
    if not full_dir.exists():
        print(f'  [SKIP] {folder}: pas de dossier full/')
        return
    print(f'\n=== {folder} ({len(entries)} entrées) ===')
    ok = fail = 0
    with open(FAIL_LOG, 'a', encoding='utf-8') as flog, \
         open(OK_LOG,   'a', encoding='utf-8') as olog:
        for entry in entries:
            num = entry[0]
            # vérifier que l'entrée a bien un fichier full/ existant
            existing = list(full_dir.glob(f'{num}.*'))
            if not existing:
                continue  # pas d'image actuelle pour cette entrée
            r2 = entry[1]
            r3 = entry[2]
            title = search_term(folder, num, str(num), r2, r3)
            url = get_url(title, 1200)
            if not url:
                print(f'  #{num} ECHEC ({title})')
                flog.write(f'{folder}\t{num}\t{title}\n')
                fail += 1
                continue
            sz = save_full(url, folder, num)
            if sz > 0:
                print(f'  #{num} OK {sz//1024}KB ({title[:40]})')
                olog.write(f'{folder}\t{num}\t{sz//1024}KB\t{title}\n')
                ok += 1
            else:
                flog.write(f'{folder}\t{num}\t{title}\n')
                fail += 1
    print(f'  → {ok} OK, {fail} FAIL')

# ── Main ──
print('=== UPGRADE ALL FULL/ TO 1200px ===')
print(f'Logs: {FAIL_LOG}, {OK_LOG}')
FAIL_LOG.write_text('', encoding='utf-8')
OK_LOG.write_text('', encoding='utf-8')

for folder, entries in LIST_DATA.items():
    if folder in SKIP or folder.endswith('_skip'):
        continue
    process_folder(folder, entries)

print('\n=== DONE ===')
print(f'Echecs: {FAIL_LOG}')
