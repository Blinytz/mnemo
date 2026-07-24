"""Round 3 : fleuves, batailles, jo, coupes, détroits avec titres EN."""
import sys, pathlib, requests, time
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image
from io import BytesIO
from lib_img import get_thumb_url

BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}

def save_full(url, folder, num):
    r = requests.get(url, headers=HEADERS, timeout=30)
    img = Image.open(BytesIO(r.content)).convert('RGB')
    img.thumbnail((1200, 1200), Image.LANCZOS)
    for old in (BASE / 'full' / folder).glob(f'{num}.*'):
        old.unlink()
    out = BASE / 'full' / folder / f'{num}.jpg'
    img.save(out, 'JPEG', quality=88)
    print(f'  #{num}: {img.size[0]}x{img.size[1]} {out.stat().st_size//1024}KB')

FIXES = {
    'fleuves_monde': [
        (1,'Nile'),(2,'Amazon River'),(3,'Yangtze River'),(4,'Mississippi River'),
        (5,'Yenisei River'),(6,'Yellow River'),(7,'Ob River'),(8,'Paraná River'),(9,'Congo River'),
        (10,'Amur River'),(11,'Lena River'),(12,'Mekong'),(13,'Niger River'),(14,'Mackenzie River'),
        (15,'Volga'),(16,'Zambezi'),(17,'Orinoco'),(18,'Euphrates'),(19,'Tigris'),
        (20,'Ganges'),(21,'Indus River'),(22,'Murray River'),(23,'Danube'),(24,'Saint Lawrence River'),
        (25,'Colorado River (United States)'),(26,'Rio Grande'),(27,'Orange River'),
        (28,'Rhine'),(29,'Senegal River'),(30,'Irrawaddy River'),
    ],
    'batailles_decisives': [
        (1,'Battle of Marathon'),(2,'Battle of Hastings'),(3,'Battle of Bouvines'),(4,'Battle of Waterloo'),
        (5,'Battle of Verdun'),(6,'Battle of Stalingrad'),(7,'Battle of Midway'),
        (8,'Battle of Dien Bien Phu'),(9,'Battle of Gaugamela'),(10,'Battle of Cannae'),
        (11,'Battle of Actium'),(12,'Battle of the Catalaunian Plains'),(13,'Battle of Yarmouk'),
        (14,'Battle of Tours'),(15,'Battle of Lepanto'),(16,'Battle of Rocroi'),(17,'Battle of Poltava'),
        (18,'Battle of Plassey'),(19,'Siege of Yorktown (1781)'),(20,'Battle of Valmy'),
        (21,'Battle of Austerlitz'),(22,'Battle of Leipzig'),(23,'Battle of Tsushima'),
        (24,'Battle of the Marne (1914)'),(25,'Battle of the Somme'),(26,'Second Battle of El Alamein'),
        (27,'Battle of Kursk'),(28,'Normandy landings'),(29,'Battle of Berlin (1945)'),
        (30,'Battle of Inchon'),(31,'Yom Kippur War'),(32,'Falklands War'),(33,'Gulf War'),
    ],
    'jo_ete': [
        (1,'1896 Summer Olympics'),(2,'1900 Summer Olympics'),(3,'1904 Summer Olympics'),
        (4,'1906 Intercalated Games'),(5,'1908 Summer Olympics'),(6,'1912 Summer Olympics'),
        (7,'1920 Summer Olympics'),(8,'1924 Summer Olympics'),(9,'1928 Summer Olympics'),
        (10,'1932 Summer Olympics'),(11,'1936 Summer Olympics'),(12,'1948 Summer Olympics'),
        (13,'1952 Summer Olympics'),(14,'1956 Summer Olympics'),(15,'1960 Summer Olympics'),
        (16,'1964 Summer Olympics'),(17,'1968 Summer Olympics'),(18,'1972 Summer Olympics'),
        (19,'1976 Summer Olympics'),(20,'1980 Summer Olympics'),(21,'1984 Summer Olympics'),
        (22,'1988 Summer Olympics'),(23,'1992 Summer Olympics'),(24,'1996 Summer Olympics'),
        (25,'2000 Summer Olympics'),(26,'2004 Summer Olympics'),(27,'2008 Summer Olympics'),
        (28,'2012 Summer Olympics'),(29,'2016 Summer Olympics'),(30,'2020 Summer Olympics'),
        (31,'2024 Summer Olympics'),(32,'2028 Summer Olympics'),
    ],
    'jo_hiver': [
        (1,'1924 Winter Olympics'),(2,'1928 Winter Olympics'),(3,'1932 Winter Olympics'),
        (4,'1936 Winter Olympics'),(5,'1948 Winter Olympics'),(6,'1952 Winter Olympics'),
        (7,'1956 Winter Olympics'),(8,'1960 Winter Olympics'),(9,'1964 Winter Olympics'),
        (10,'1968 Winter Olympics'),(11,'1972 Winter Olympics'),(12,'1976 Winter Olympics'),
        (13,'1980 Winter Olympics'),(14,'1984 Winter Olympics'),(15,'1988 Winter Olympics'),
        (16,'1992 Winter Olympics'),(17,'1994 Winter Olympics'),(18,'1998 Winter Olympics'),
        (19,'2002 Winter Olympics'),(20,'2006 Winter Olympics'),(21,'2010 Winter Olympics'),
        (22,'2014 Winter Olympics'),(23,'2018 Winter Olympics'),(24,'2022 Winter Olympics'),
        (25,'2026 Winter Olympics'),
    ],
    'coupes_monde': [
        (1,'1930 FIFA World Cup'),(2,'1934 FIFA World Cup'),(3,'1938 FIFA World Cup'),
        (4,'1950 FIFA World Cup'),(5,'1954 FIFA World Cup'),(6,'1958 FIFA World Cup'),
        (7,'1962 FIFA World Cup'),(8,'1966 FIFA World Cup'),(9,'1970 FIFA World Cup'),
        (10,'1974 FIFA World Cup'),(11,'1978 FIFA World Cup'),(12,'1982 FIFA World Cup'),
        (13,'1986 FIFA World Cup'),(14,'1990 FIFA World Cup'),(15,'1994 FIFA World Cup'),
        (16,'1998 FIFA World Cup'),(17,'2002 FIFA World Cup'),(18,'2006 FIFA World Cup'),
        (19,'2010 FIFA World Cup'),(20,'2014 FIFA World Cup'),(21,'2018 FIFA World Cup'),
        (22,'2022 FIFA World Cup'),(23,'2026 FIFA World Cup'),
    ],
    'detroits_monde': [
        (1,'Strait of Gibraltar'),(2,'Bosphorus'),(3,'Dardanelles'),(4,'Strait of Hormuz'),
        (5,'Strait of Malacca'),(6,'Bering Strait'),(7,'Strait of Magellan'),
        (8,'Bab-el-Mandeb'),(9,'Strait of Dover'),(10,'Strait of Messina'),
        (11,'Skagerrak'),(12,'Taiwan Strait'),(13,'Korea Strait'),(14,'Lombok Strait'),
        (15,'Bass Strait'),(16,'Straits of Florida'),(17,'Øresund'),
        (18,'Mozambique Channel'),(19,'Singapore Strait'),(20,'Tsugaru Strait'),
    ],
}

for folder, entries in FIXES.items():
    print(f'\n=== {folder} ===')
    for num, title in entries:
        existing = list((BASE / 'full' / folder).glob(f'{num}.*'))
        if not existing:
            pass  # on crée quand même si pas existant
        url = get_thumb_url(title, 1200)
        if url:
            save_full(url, folder, num)
        else:
            print(f'  #{num} ECHEC ({title})')

print('\nDone.')
