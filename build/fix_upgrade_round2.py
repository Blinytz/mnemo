"""
Round 2 :
  1) Recompresse les images > 2MB à 1200px q88
  2) Re-télécharge les échecs avec des titres EN corrects
"""
import sys, pathlib, requests, time
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO
from lib_img import get_thumb_url

BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}

def cap_image(path):
    """Recompresse une image trop grande à max 1200px."""
    img = Image.open(path).convert('RGB')
    w, h = img.size
    if w <= 1200 and h <= 1200:
        return
    img.thumbnail((1200, 1200), Image.LANCZOS)
    out = path.with_suffix('.jpg')
    img.save(out, 'JPEG', quality=88)
    if out != path:
        path.unlink()
    print(f'  Compressé: {path.name} {w}x{h} → {img.size[0]}x{img.size[1]} {out.stat().st_size//1024}KB')

def save_full(url, folder, num):
    r = requests.get(url, headers=HEADERS, timeout=30)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img.thumbnail((1200, 1200), Image.LANCZOS)
    # Supprimer l'ancien fichier si extension différente
    for old in (BASE / 'full' / folder).glob(f'{num}.*'):
        old.unlink()
    out = BASE / 'full' / folder / f'{num}.jpg'
    img.save(out, 'JPEG', quality=88)
    print(f'  #{num}: {img.size[0]}x{img.size[1]} {out.stat().st_size//1024}KB')
    return True

# ═══ 1) RECOMPRESSER LES GÉANTS ═══
print('=== RECOMPRESSION IMAGES > 2MB ===')
FULL = BASE / 'full'
for f in FULL.rglob('*'):
    if f.is_file() and f.suffix in ('.jpg','.jpeg','.png','.webp') and f.stat().st_size > 2_000_000:
        print(f'  {f.relative_to(FULL)}')
        cap_image(f)

# ═══ 2) RE-TÉLÉCHARGER ÉCHECS AVEC TITRES EN ═══

# Littérature : titres anglais
LIT_EN = [
    (1,'Iliad'),(2,'Odyssey'),(3,'Aeneid'),(4,'Metamorphoses (Ovid)'),
    (5,'Divine Comedy'),(6,'The Decameron'),(10,'King Lear'),(11,'Essays (Montaigne)'),
    (15,'The Red and the Black'),(16,'The Charterhouse of Parma'),(17,'Père Goriot'),
    (19,'Crime and Punishment'),(20,'The Brothers Karamazov'),(21,'War and Peace'),
    (22,'Anna Karenina'),(24,'Adventures of Huckleberry Finn'),(25,'Moby-Dick'),
    (26,'Wuthering Heights'),(27,'Jane Eyre'),(28,'The Picture of Dorian Gray'),
    (29,'In Search of Lost Time'),(30,'Ulysses (novel)'),(33,'The Stranger (Camus novel)'),
    (34,'Nausea (Sartre)'),(35,'The Trial (novel)'),(38,'Animal Farm'),
    (39,'Brave New World'),(41,'The Lord of the Rings'),(42,'The Catcher in the Rye'),
    (43,'On the Road'),(44,'One Hundred Years of Solitude'),(45,'The Master and Margarita'),
    (47,'The Sound and the Fury'),(48,'Beloved (novel)'),(49,'The Name of the Rose'),
    (50,'The Grapes of Wrath'),(51,'The Flowers of Evil'),(52,'Journey to the End of the Night'),
    (53,"Man's Fate"),(54,'Dune (novel)'),(55,'Foundation (Asimov)'),(56,'The Hitchhiker\'s Guide to the Galaxy'),
    (57,'Harry Potter'),(58,'The Alchemist (novel)'),(59,'L\'Assommoir'),(60,'Invisible Man (Ellison novel)'),
]

print('\n=== LITTÉRATURE (titres EN) ===')
for num, title in LIT_EN:
    existing = list((BASE/'full'/'litterature').glob(f'{num}.*'))
    url = get_thumb_url(title, 1200)
    if url:
        save_full(url, 'litterature', num)
    else:
        print(f'  #{num} ECHEC ({title})')

# Peintres : noms EN
PEINTRES_EN = [
    (1,'Jan van Eyck'),(2,'Sandro Botticelli'),(3,'Leonardo da Vinci'),(4,'Albrecht Dürer'),
    (5,'Michelangelo'),(6,'Raphael (painter)'),(7,'Titian'),(8,'Pieter Bruegel the Elder'),
    (9,'Caravaggio'),(11,'Nicolas Poussin'),(13,'Johannes Vermeer'),(14,'Francisco Goya'),
    (15,'Jacques-Louis David'),(16,'Caspar David Friedrich'),(17,'Eugène Delacroix'),
    (18,'Gustave Courbet'),(19,'Édouard Manet'),(33,'Edward Hopper'),(34,'Amedeo Modigliani'),
    (35,'Diego Rivera'),(36,'Marcel Duchamp'),(37,'Giorgio de Chirico'),
]
print('\n=== PEINTRES (noms EN) ===')
for num, title in PEINTRES_EN:
    url = get_thumb_url(title, 1200)
    if url:
        save_full(url, 'peintres', num)
    else:
        print(f'  #{num} ECHEC ({title})')

# Rois de France : noms EN
ROIS_EN = [
    (1,'Clovis I'),(2,'Chlothar I'),(3,'Chilperic I'),(4,'Chlothar II'),(5,'Dagobert I'),
    (6,'Clovis II'),(7,'Chlothar III'),(8,'Theuderic III'),(9,'Clovis IV'),(10,'Childebert III'),
    (11,'Dagobert III'),(12,'Chilperic II'),(13,'Theuderic IV'),(14,'Childeric III'),
    (15,'Pepin the Short'),(17,'Louis the Pious'),(18,'Charles the Bald'),(19,'Louis the Stammerer'),
    (20,'Louis III of France'),(21,'Carloman II'),(22,'Charles the Fat'),(23,'Odo, Count of Paris'),
    (24,'Charles the Simple'),(25,'Robert I of France'),(26,'Rudolph of France'),
    (27,'Louis IV of France'),(28,'Lothair of France'),(29,'Louis V of France'),
    (31,'Robert II of France'),(32,'Henry I of France'),(33,'Philip I of France'),
    (34,'Louis VI of France'),(35,'Louis VII of France'),(36,'Philip II of France'),
    (37,'Louis VIII of France'),(38,'Louis IX of France'),(39,'Philip III of France'),
    (40,'Philip IV of France'),(41,'Louis X of France'),(42,'John I of France'),
    (43,'Philip V of France'),(44,'Charles IV of France'),(45,'Philip VI of France'),
    (46,'John II of France'),(47,'Charles V of France'),(48,'Charles VI of France'),
    (49,'Charles VII of France'),(51,'Charles VIII of France'),(52,'Louis XII of France'),
    (53,'Francis I of France'),(54,'Henry II of France'),(55,'Francis II of France'),
    (56,'Charles IX of France'),(57,'Henry III of France'),(58,'Henry IV of France'),
    (59,'Louis XIII'),(61,'Louis XV'),(62,'Louis XVI'),
    (63,'Napoleon'),(64,'Louis XVIII'),(65,'Charles X'),(66,'Louis Philippe I'),
]
print('\n=== ROIS DE FRANCE (noms EN) ===')
for num, title in ROIS_EN:
    url = get_thumb_url(title, 1200)
    if url:
        save_full(url, 'rois_france', num)
    else:
        print(f'  #{num} ECHEC ({title})')

# Mythologie : noms EN
MYTH_EN = [
    (1,'Zeus'),(2,'Hera'),(3,'Poseidon'),(4,'Demeter'),(5,'Athena'),
    (6,'Apollo'),(7,'Artemis'),(8,'Ares'),(9,'Aphrodite'),(10,'Hephaestus'),
    (11,'Hermes'),(12,'Dionysus'),(13,'Hades'),(14,'Persephone'),(15,'Hestia'),
    (16,'Nyx'),(17,'Chaos (cosmogony)'),(18,'Cronus'),(19,'Hecate'),(20,'Thanatos'),
    (21,'Hypnos'),(22,'Charon (mythology)'),(23,'Eros'),(24,'Nike (mythology)'),
    (25,'Prometheus'),(26,'Atlas (mythology)'),(32,'Heracles'),(33,'Achilles'),
    (34,'Odysseus'),(35,'Theseus'),(36,'Minotaur'),(37,'Orpheus'),(38,'Eurydice (mythology)'),
    (39,'Sisyphus'),(40,'Perseus'),(41,'Medusa'),(42,'Icarus'),(43,'Daedalus'),
    (44,'Narcissus (mythology)'),(45,'Echo (mythology)'),(46,'Arachne'),(47,'Oedipus'),
    (48,'Pandora'),(49,'Eris (mythology)'),(50,'Helios'),(51,'Selene'),(52,'Tyche'),
    (53,'Aeolus'),(54,'Cerberus'),(55,'Medea'),(57,'Tantalus'),(58,'Ixion'),
    (59,'Hyperion (mythology)'),
]
print('\n=== MYTHOLOGIE (noms EN) ===')
for num, title in MYTH_EN:
    url = get_thumb_url(title, 1200)
    if url:
        save_full(url, 'mythologie', num)
    else:
        print(f'  #{num} ECHEC ({title})')

print('\nDone.')
