"""
Reconstruction complète full/ via Wikimedia Commons search API.
Qualité 1200px JPEG q88. Skip : pays, departements, etats_usa, elements,
periodes_geologiques, vocabulaire_precis, phrasal_verbs, os.
"""
import sys, pathlib, requests, time, csv, re
from PIL import Image
from io import BytesIO

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE  = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')
FULL  = BASE / 'full'
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://commons.wikimedia.org/',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
}
SKIP = {'pays','departements','etats_usa','elements','periodes_geologiques',
        'vocabulaire_precis','phrasal_verbs','os'}

Image.MAX_IMAGE_PIXELS = None  # évite DecompressionBombWarning

LOG = open(BASE/'build'/'commons_results.csv','w',newline='',encoding='utf-8')
csv_w = csv.writer(LOG)
csv_w.writerow(['folder','num','query','file','width','height','kb','score'])
FAIL = open(BASE/'build'/'commons_fails.txt','w',encoding='utf-8')

def search_commons(query, min_px=600):
    """Cherche sur Commons, retourne liste triée (w*h desc) de (w,h,url,title)."""
    for attempt in range(3):
        try:
            r = requests.get(COMMONS_API, params={
                'action':'query','generator':'search',
                'gsrnamespace':6,'gsrlimit':10,'gsrsearch':query,
                'prop':'imageinfo','iiprop':'url|size','iiurlwidth':1200,
                'format':'json'
            }, headers=HEADERS, timeout=25)
            if r.status_code == 429:
                time.sleep(10 + attempt*5)
                continue
            time.sleep(1.5)
            pages = r.json().get('query',{}).get('pages',{})
            break
        except Exception as e:
            time.sleep(5)
            if attempt == 2:
                return [], str(e)
    else:
        return [], 'max retries'

    valid = []
    for p in pages.values():
        info = p.get('imageinfo',[{}])[0]
        w, h = info.get('width',0), info.get('height',0)
        thumb = info.get('thumburl','')
        orig  = info.get('url','')
        url   = thumb or orig
        title = p.get('title','')
        # Filtrer SVG et trop petites
        if not url:
            continue
        ext = (thumb or orig).lower().split('?')[0].split('/')[-1]
        if ext.endswith('.svg') or ext.endswith('.ogg') or ext.endswith('.webm'):
            continue
        if w >= min_px or h >= min_px:
            valid.append((w*h, w, h, url, orig, title))
    valid.sort(reverse=True)
    return valid, None

def download_url(url):
    """Télécharge une URL. Retourne (content, None) ou (None, err)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        time.sleep(2.5)  # pause après chaque download pour éviter 429
        if resp.status_code == 429:
            return None, '429'
        if resp.status_code != 200:
            return None, f'HTTP {resp.status_code}'
        if len(resp.content) < 3000:
            return None, 'trop court'
        return resp.content, None
    except Exception as e:
        return None, str(e)[:60]

def download_save(folder, num, thumb_url, orig_url):
    """Télécharge, redimensionne, sauvegarde."""
    for url in [u for u in [thumb_url, orig_url] if u]:
        content, err = download_url(url)
        if not content:
            continue
        try:
            img = Image.open(BytesIO(content)).convert('RGB')
            w0, h0 = img.size
            if max(w0, h0) < 400:
                continue
            img.thumbnail((1200, 1200), Image.LANCZOS)
            for old in (FULL/folder).glob(f'{num}.*'):
                old.unlink()
            out = FULL/folder/f'{num}.jpg'
            img.save(out, 'JPEG', quality=88, optimize=True)
            fw, fh = img.size
            kb = out.stat().st_size // 1024
            return (w0, h0, fw, fh, kb), None
        except Exception:
            continue
    return None, 'échec'

def process(folder, entries):
    """entries: dict {num: (display_name, query_string)}"""
    (FULL/folder).mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    print(f'\n=== {folder} ({len(entries)}) ===', flush=True)
    for num, (name, query) in sorted(entries.items()):
        results, err = search_commons(query)
        if not results:
            # fallback: requête simplifiée
            short = ' '.join(query.split()[:3])
            results, err2 = search_commons(short)
        if not results:
            print(f'  #{num:3d} RIEN — {name}')
            FAIL.write(f'{folder}\t{num}\t{name}\t{query}\tno results\n')
            FAIL.flush()
            fail += 1
            continue
        saved = False
        for _, w, h, thumb_url, orig_url, title in results[:5]:
            res, err = download_save(folder, num, thumb_url, orig_url)
            if res:
                w0, h0, fw, fh, kb = res
                score = min(10, max(fw,fh)//120)
                note = '✓' if score>=8 else ('~' if score>=5 else '⚠')
                print(f'  #{num:3d} {note} {fw}x{fh} {kb:3d}KB  {name}')
                csv_w.writerow([folder,num,query,title,fw,fh,kb,score])
                LOG.flush()
                ok += 1; saved = True; break
        if not saved:
            print(f'  #{num:3d} ECHEC — {name}')
            FAIL.write(f'{folder}\t{num}\t{name}\t{query}\tdownload failed\n')
            FAIL.flush()
            fail += 1
    print(f'  → {ok} OK / {fail} échecs', flush=True)
    return ok, fail

# ─────────────────────────────────────────────────────────────────
# Données par liste : {num: (nom_affichage, requête_commons)}
# ─────────────────────────────────────────────────────────────────
LISTS = {}

LISTS['peintres'] = {
    1:  ('Jan van Eyck',        'Ghent Altarpiece polyptych painting Eyck'),
    2:  ('Botticelli',          'Birth of Venus Botticelli painting Uffizi'),
    3:  ('Léonard de Vinci',    'Mona Lisa Leonardo da Vinci painting Louvre'),
    4:  ('Albrecht Dürer',      'Durer self portrait painting 1500'),
    5:  ('Michel-Ange',         'Michelangelo Sistine Chapel ceiling fresco'),
    6:  ('Raphaël',             'Raphael School of Athens fresco Vatican'),
    7:  ('Titien',              'Titian Venus of Urbino painting Uffizi'),
    8:  ("Bruegel l'Ancien",    'Bruegel Tower of Babel painting'),
    9:  ('Caravage',            'Caravaggio Judith Beheading Holofernes painting'),
    10: ('Rembrandt',           'Rembrandt Night Watch painting Rijksmuseum'),
    11: ('Nicolas Poussin',     'Nicolas Poussin Arcadian Shepherds painting Louvre'),
    12: ('Vermeer',             'Vermeer Girl with Pearl Earring painting'),
    13: ('Francisco Goya',      'Goya Third of May 1808 painting Prado'),
    14: ('Jacques-Louis David', 'David Napoleon crossing Alps painting'),
    15: ('Caspar David Friedrich','Friedrich Wanderer above Sea of Fog painting'),
    16: ('Eugène Delacroix',    'Delacroix Liberty Leading the People painting'),
    17: ('Gustave Courbet',     'Courbet Stone Breakers realist painting'),
    18: ('Édouard Manet',       'Manet Olympia painting Musée Orsay'),
    19: ('Claude Monet',        'Monet Water Lilies Nympheas painting'),
    20: ('Pierre-Auguste Renoir','Renoir Moulin de la Galette painting'),
    21: ('Edgar Degas',         'Degas ballet dancers painting'),
    22: ('Paul Cézanne',        'Cézanne Mont Sainte-Victoire painting'),
    23: ('Georges Seurat',      'Seurat Sunday Afternoon Grande Jatte painting'),
    24: ('Vincent van Gogh',    'Van Gogh Starry Night painting MoMA'),
    25: ('Paul Gauguin',        'Gauguin Tahiti women painting'),
    26: ('Toulouse-Lautrec',    'Toulouse-Lautrec Moulin Rouge poster'),
    27: ('Gustav Klimt',        'Klimt The Kiss painting gold'),
    28: ('Edvard Munch',        'Edvard Munch The Scream painting'),
    29: ('Henri Matisse',       'Matisse Dance painting colorful'),
    30: ('Pablo Picasso',       'Picasso Guernica painting large'),
    31: ('Wassily Kandinsky',   'Kandinsky Composition abstract painting'),
    32: ('Edward Hopper',       'Hopper Nighthawks painting'),
    33: ('Amedeo Modigliani',   'Modigliani Reclining Nude portrait painting'),
    34: ('Diego Rivera',        'Diego Rivera mural fresco Mexico'),
    35: ('Marcel Duchamp',      'Duchamp Fountain readymade art'),
    36: ('Giorgio de Chirico',  'Chirico metaphysical painting city street'),
    37: ('René Magritte',       'Magritte Son of Man painting surrealism'),
    38: ('Salvador Dalí',       'Dali Persistence of Memory painting surrealism'),
    39: ('Frida Kahlo',         'Frida Kahlo self portrait painting'),
    40: ('Jackson Pollock',     'Jackson Pollock Number 31 drip painting MoMA'),
    41: ('Mark Rothko',         'Rothko No 61 color field painting'),
    42: ('Andy Warhol',         'Warhol Marilyn Diptych pop art'),
    43: ('Roy Lichtenstein',    'Lichtenstein Whaam comic pop art painting'),
    44: ('Francis Bacon',       'Francis Bacon Three Studies Lucian Freud painting'),
    45: ('Lucian Freud',        'Lucian Freud Benefits Supervisor Sleeping painting'),
    46: ('David Hockney',       'Hockney A Bigger Splash painting Tate'),
    47: ('Gerhard Richter',     'Gerhard Richter abstract photorealism painting'),
    48: ('Jean-Michel Basquiat','Basquiat painting graffiti street art'),
    49: ('Banksy',              'Banksy Girl with Balloon street art'),
    50: ('Rembrandt 2',         'Rembrandt self portrait old age painting'),
}

LISTS['musees_monde'] = {
    1:  ('Louvre',              'Louvre Museum Paris pyramid exterior'),
    2:  ('Metropolitan',        'Metropolitan Museum Art New York exterior Fifth Avenue'),
    3:  ('British Museum',      'British Museum London Great Court interior'),
    4:  ('Ermitage',            'Hermitage Museum Saint Petersburg exterior facade'),
    5:  ('Musées du Vatican',   'Vatican Museums Rome Sistine Chapel aerial'),
    6:  ('Offices de Florence', 'Uffizi Gallery Florence exterior Piazzale degli'),
    7:  ('Prado',               'Prado Museum Madrid exterior building'),
    8:  ('Rijksmuseum',         'Rijksmuseum Amsterdam exterior canal reflection'),
    9:  ("Musée d'Orsay",       'Musée Orsay Paris exterior former train station'),
    10: ('Tate Modern',         'Tate Modern London exterior Thames Bankside'),
    11: ('MoMA',                'Museum Modern Art MoMA New York interior atrium'),
    12: ('Guggenheim Bilbao',   'Guggenheim Museum Bilbao exterior titanium'),
    13: ('National Gallery',    'National Gallery London Trafalgar Square exterior'),
    14: ('Smithsonian',         'Smithsonian Institution Washington DC National Mall'),
    15: ("Musée de l'Acropole", 'Acropolis Museum Athens new building exterior'),
    16: ('Musée égyptien du Caire','Egyptian Museum Cairo Tahrir Square exterior'),
    17: ('Tokyo National',      'Tokyo National Museum Ueno Park exterior Japan'),
    18: ('Musée national de Chine','National Museum China Beijing exterior Tiananmen'),
    19: ('Pergamon',            'Pergamon Museum Berlin Ishtar Gate'),
    20: ('Galerie de Dresde',   'Gemäldegalerie Alte Meister Dresden Zwinger'),
    21: ('Pinacothèque Brera',  'Pinacoteca di Brera Milan exterior courtyard'),
    22: ('Palais de Topkapi',   'Topkapi Palace Istanbul exterior aerial Turkey'),
    23: ('Versailles',          'Palace Versailles aerial gardens Hall Mirrors'),
    24: ('Pompidou',            'Centre Georges Pompidou Paris exterior colorful pipes'),
    25: ('Stedelijk',           'Stedelijk Museum Amsterdam exterior modern'),
}

LISTS['parcs_nationaux'] = {
    1:  ('Yellowstone',         'Yellowstone Grand Prismatic Spring aerial'),
    2:  ('Grand Canyon',        'Grand Canyon Colorado River aerial view'),
    3:  ('Yosemite',            'Yosemite Valley El Capitan Half Dome'),
    4:  ('Grande Barrière de Corail','Great Barrier Reef aerial coral Queensland'),
    5:  ('Serengeti',           'Serengeti savanna Tanzania wildebeest migration aerial'),
    6:  ('Amazonie',            'Amazon rainforest river aerial Brazil'),
    7:  ('Torres del Paine',    'Torres del Paine Patagonia Chile mountains'),
    8:  ('Galápagos',           'Galapagos Islands Ecuador giant tortoise iguana'),
    9:  ('Fiordland',           'Fiordland National Park Milford Sound New Zealand'),
    10: ('Banff',               'Banff National Park Lake Louise turquoise Canada'),
    11: ('Kruger',              'Kruger National Park South Africa elephant lion'),
    12: ('Everglades',          'Everglades National Park aerial wetlands Florida'),
    13: ('Machu Picchu',        'Machu Picchu Inca ruins aerial Peru'),
    14: ('Zhangjiajie',         'Zhangjiajie Hunan China sandstone pillars aerial'),
    15: ('Komodo',              'Komodo dragon Indonesia island'),
    16: ('Kilimandjaro',        'Mount Kilimanjaro aerial Tanzania snow summit'),
    17: ('Iguazu',              'Iguazu Falls aerial waterfall Argentina Brazil'),
    18: ('Denali',              'Denali Mount McKinley Alaska aerial'),
    19: ('Glacier',             'Glacier National Park Montana lakes mountains USA'),
    20: ('Arches',              'Arches National Park Utah Delicate Arch sandstone'),
    21: ('Tongariro',           'Tongariro National Park volcanic New Zealand'),
    22: ('Dolomites',           'Dolomites Italy mountain peaks landscape alpine'),
    23: ('Cévennes',            'Cévennes National Park France landscape'),
    24: ('Lake District',       'Lake District England Windermere lake landscape'),
    25: ('Baie d\'Halong',      'Ha Long Bay Vietnam karst limestone aerial'),
}

LISTS['compositeurs'] = {
    1:  ('Bach',            'Johann Sebastian Bach portrait painting composer'),
    2:  ('Haendel',         'George Frideric Handel portrait painting composer'),
    3:  ('Vivaldi',         'Antonio Vivaldi portrait painting baroque composer'),
    4:  ('Mozart',          'Wolfgang Amadeus Mozart portrait painting classical composer'),
    5:  ('Beethoven',       'Ludwig van Beethoven portrait painting composer'),
    6:  ('Schubert',        'Franz Schubert portrait painting Austrian composer'),
    7:  ('Chopin',          'Frédéric Chopin portrait romantic composer piano'),
    8:  ('Schumann',        'Robert Schumann portrait painting composer'),
    9:  ('Liszt',           'Franz Liszt portrait composer pianist'),
    10: ('Wagner',          'Richard Wagner portrait photograph opera composer'),
    11: ('Verdi',           'Giuseppe Verdi portrait photograph opera Italian'),
    12: ('Brahms',          'Johannes Brahms portrait photograph composer'),
    13: ('Dvořák',          'Antonín Dvořák portrait photograph Czech composer'),
    14: ('Tchaïkovski',     'Tchaikovsky portrait photograph Russian composer'),
    15: ('Puccini',         'Giacomo Puccini portrait photograph opera'),
    16: ('Mahler',          'Gustav Mahler portrait photograph Viennese composer'),
    17: ('Debussy',         'Claude Debussy portrait photograph French composer'),
    18: ('Ravel',           'Maurice Ravel portrait photograph French composer'),
    19: ('Stravinsky',      'Igor Stravinsky portrait photograph composer'),
    20: ('Bartók',          'Béla Bartók portrait photograph Hungarian composer'),
    21: ('Prokofiev',       'Sergei Prokofiev portrait photograph Soviet composer'),
    22: ('Chostakovitch',   'Dmitri Shostakovich portrait photograph composer'),
    23: ('Schoenberg',      'Arnold Schoenberg portrait photograph composer'),
    24: ('Alban Berg',      'Alban Berg portrait photograph Austrian composer'),
    25: ('Webern',          'Anton Webern portrait photograph Austrian composer'),
}

LISTS['mouvements_peinture'] = {
    1:  ('Art byzantin',        'Byzantine mosaic art Ravenna gold Christ Pantocrator'),
    2:  ('Art roman',           'Romanesque art church fresco abbey'),
    3:  ('Art gothique',        'Gothic stained glass cathedral rose window Notre-Dame'),
    4:  ('Primitifs flamands',  'Early Flemish painting van Eyck Annunciation altar'),
    5:  ('Renaissance italienne','Italian Renaissance Raphael Botticelli painting'),
    6:  ('Maniérisme',          'Mannerism Pontormo Bronzino elongated figures painting'),
    7:  ('Baroque',             'Baroque Caravaggio dramatic light shadow chiaroscuro'),
    8:  ("Âge d'or néerlandais",'Dutch Golden Age Vermeer Rembrandt interior light'),
    9:  ('Rococo',              'Rococo Fragonard Watteau painting elegant pastoral'),
    10: ('Néoclassicisme',      'Neoclassicism Jacques-Louis David Greek Roman'),
    11: ('Romantisme',          'Romanticism Delacroix dramatic nature sublime painting'),
    12: ('Réalisme',            'Realism Courbet Millet peasants everyday life painting'),
    13: ("École de Barbizon",   'Barbizon school Corot Millet landscape forest painting'),
    14: ('Préraphaélisme',      'Pre-Raphaelite Millais Ophelia painting'),
    15: ('Impressionnisme',     'Impressionism Monet outdoor light color painting'),
    16: ('Post-impressionnisme','Post-Impressionism Van Gogh Cézanne Gauguin painting'),
    17: ('Symbolisme',          'Symbolism Gustave Moreau mysterious allegory painting'),
    18: ('Art nouveau',         'Art Nouveau Klimt Mucha organic decorative'),
    19: ('Fauvisme',            'Fauvism Matisse Derain bold bright color painting'),
    20: ('Expressionnisme',     'Expressionism Die Brücke Kirchner Munch color distort'),
    21: ('Cubisme',             'Cubism Picasso Braque Les Demoiselles d\'Avignon'),
    22: ('Futurisme',           'Futurism Balla Boccioni dynamic movement painting'),
    23: ('Constructivisme',     'Constructivism Russian El Lissitzky Rodchenko abstract'),
    24: ('De Stijl',            'De Stijl Mondrian Composition red blue yellow'),
    25: ('Dadaïsme',            'Dada Duchamp anti-art readymade Fountain'),
    26: ('Surréalisme',         'Surrealism Dalí dreamlike painting'),
    27: ('Expressionnisme abstrait','Abstract expressionism Pollock drip painting large'),
    28: ('Pop Art',             'Pop Art Warhol Campbell soup print silk screen'),
    29: ('Minimalisme',         'Minimalism Donald Judd sculpture geometric'),
    30: ('Art conceptuel',      'Conceptual art installation text idea'),
    31: ('Hyperréalisme',       'Hyperrealism photorealistic Chuck Close painting'),
    32: ('Street art',          'street art mural urban graffiti colorful'),
    33: ('Abstraction lyrique', 'Abstract lyrical painting Hans Hartung Soulages'),
    34: ('Néo-expressionnisme', 'Neo-expressionism Basquiat Kiefer raw painting'),
    35: ('Arte Povera',         'Arte Povera Jannis Kounellis raw materials installation'),
    36: ('Fluxus',              'Fluxus Beuys performance happening art event'),
}

LISTS['architectes_majeurs'] = {
    1:  ('Brunelleschi',    'Brunelleschi Florence Cathedral dome cupola exterior'),
    2:  ('Palladio',        'Palladio Villa Rotonda Vicenza architecture'),
    3:  ('Gaudí',           'Gaudí Sagrada Familia Barcelona exterior'),
    4:  ('Frank Lloyd Wright','Fallingwater Wright house architecture Pennsylvania'),
    5:  ('Le Corbusier',    'Le Corbusier Villa Savoye Poissy modernist'),
    6:  ('Mies van der Rohe','Mies van der Rohe Barcelona Pavilion glass steel'),
    7:  ('Zaha Hadid',      'Zaha Hadid MAXXI Rome futuristic building'),
    8:  ('I. M. Pei',       'IM Pei Louvre Pyramid glass exterior'),
    9:  ('Michel-Ange',     "Michelangelo Saint Peter's Basilica dome Rome exterior"),
    10: ('Christopher Wren', "Wren Saint Paul's Cathedral London dome exterior"),
    11: ('Balthasar Neumann','Balthasar Neumann Würzburg Residence staircase'),
    12: ('Charles Garnier', 'Paris Opéra Garnier exterior grand facade'),
    13: ('Victor Horta',    'Victor Horta Hotel Tassel Art Nouveau staircase'),
    14: ('Walter Gropius',  'Bauhaus Dessau building Gropius architecture'),
    15: ('Alvar Aalto',     'Alvar Aalto Villa Mairea organic architecture Finland'),
    16: ('Oscar Niemeyer',  'Niemeyer National Congress Brasilia dome'),
    17: ('Louis Kahn',      'Louis Kahn Salk Institute La Jolla courtyard'),
    18: ('Renzo Piano',     'Renzo Piano Centre Pompidou Paris exterior'),
    19: ('Norman Foster',   'Norman Foster 30 St Mary Axe Gherkin London'),
    20: ('Frank Gehry',     'Gehry Guggenheim Museum Bilbao titanium curves'),
    21: ('Tadao Ando',      'Tadao Ando concrete architecture Church of Light'),
    22: ('Jean Nouvel',     "Jean Nouvel Institut du Monde Arabe Paris mashrabiya"),
    23: ('Rem Koolhaas',    'Rem Koolhaas CCTV Headquarters Beijing tower'),
    24: ('Santiago Calatrava','Calatrava Città della Musica Valencia bridge white'),
    25: ('Herzog & de Meuron','Tate Modern Herzog de Meuron London exterior'),
    26: ('Kengo Kuma',      'Kengo Kuma Japan National Stadium wood architecture'),
    27: ('Dominique Perrault','Bibliothèque nationale France Perrault towers'),
    28: ('Carlo Scarpa',    'Carlo Scarpa Castelvecchio museum Verona'),
    29: ('Richard Rogers',  "Richard Rogers Lloyd's Building London exterior"),
    30: ('Bjarke Ingels',   'Bjarke Ingels Group 8 House Copenhagen architecture'),
}

LISTS['decouvertes_scientifiques'] = {
    1:  ('Héliocentrisme',  'Copernicus heliocentric system diagram sun center'),
    2:  ('Gravitation',     'Newton gravitation apple law universal gravity portrait'),
    3:  ('Calcul infinitésimal','calculus Newton Leibniz manuscript mathematics differential'),
    4:  ('Thermodynamique', 'Watt steam engine thermodynamics industrial revolution'),
    5:  ('Électromagnétisme','Faraday electromagnetic induction experiment coil magnet'),
    6:  ('Évolution',       'Darwin On Origin Species evolution tree of life illustration'),
    7:  ('Germes',          'Pasteur germ theory experiment bacteriology laboratory'),
    8:  ('Tableau périodique','Mendeleev periodic table elements chemistry wall 1869'),
    9:  ('Rayons X',        'X-ray radiography hand bones Röntgen Wilhelm 1895'),
    10: ('Radioactivité',   'Marie Curie radioactivity laboratory uranium portrait'),
    11: ('Relativité',      'Einstein relativity theory portrait photograph chalkboard'),
    12: ('Mécanique quantique','quantum mechanics atom Bohr model electron orbital'),
    13: ('ADN',             'DNA double helix model Watson Crick molecular biology'),
    14: ('Pénicilline',     'Alexander Fleming penicillin mold Petri dish antibiotic'),
    15: ('Big Bang',        'Big Bang cosmic microwave background radiation universe map'),
    16: ('Tectonique des plaques','plate tectonics Pangaea continental drift map reconstruction'),
    17: ('Boson de Higgs',  'Higgs boson particle physics CERN LHC collision'),
    18: ('Ondes gravitationnelles','gravitational waves LIGO interferometer merger black hole'),
    19: ('CRISPR',          'CRISPR Cas9 gene editing DNA scissors diagram molecular'),
    20: ('Exoplanètes',     'exoplanet transit Kepler telescope planet star light curve'),
}

LISTS['grands_scientifiques'] = {
    1:  ('Newton',          'Isaac Newton portrait painting physicist mathematician'),
    2:  ('Galilée',         'Galileo Galilei portrait painting telescope astronomer'),
    3:  ('Einstein',        'Albert Einstein portrait photograph physicist'),
    4:  ('Darwin',          'Charles Darwin portrait photograph naturalist'),
    5:  ('Marie Curie',     'Marie Curie portrait laboratory photograph Nobel'),
    6:  ('Pasteur',         'Louis Pasteur portrait photograph bacteriologist'),
    7:  ('Tesla',           'Nikola Tesla portrait photograph electricity inventor'),
    8:  ('Faraday',         'Michael Faraday portrait painting physicist'),
    9:  ('Maxwell',         'James Clerk Maxwell portrait painting physicist'),
    10: ('Planck',          'Max Planck portrait photograph physicist Nobel'),
    11: ('Bohr',            'Niels Bohr portrait photograph physicist atom'),
    12: ('Heisenberg',      'Werner Heisenberg portrait photograph physicist uncertainty'),
    13: ('Feynman',         'Richard Feynman portrait photograph blackboard physicist'),
    14: ('Schrödinger',     'Erwin Schrödinger portrait photograph physicist Nobel'),
    15: ('Mendel',          'Gregor Mendel portrait painting genetics pea monk'),
    16: ('Kepler',          'Johannes Kepler portrait painting astronomer planetary'),
    17: ('Descartes',       'René Descartes portrait painting philosopher mathematician'),
    18: ('Pascal',          'Blaise Pascal portrait painting mathematician physicist'),
    19: ('Euler',           'Leonhard Euler portrait painting Swiss mathematician'),
    20: ('Gauss',           'Carl Friedrich Gauss portrait painting German mathematician'),
    21: ('James Watt',      'James Watt steam engine inventor portrait painting'),
    22: ('Lavoisier',       'Antoine Lavoisier chemistry laboratory portrait'),
    23: ('Humphry Davy',    'Humphry Davy portrait chemist sodium potassium'),
    24: ('Volta',           'Alessandro Volta battery portrait physicist'),
    25: ('Ampère',          'André-Marie Ampère portrait physicist electromagnetism'),
    26: ('Joule',           'James Prescott Joule portrait physicist thermodynamics'),
    27: ('Lord Kelvin',     'Lord Kelvin portrait physicist temperature scale'),
    28: ('Hertz',           'Heinrich Hertz portrait physicist radio waves'),
    29: ('Röntgen',         'Wilhelm Röntgen portrait physicist X-ray Nobel'),
    30: ('Rutherford',      'Ernest Rutherford portrait physicist nuclear atom'),
    31: ('Fermi',           'Enrico Fermi portrait physicist nuclear reactor'),
    32: ('Oppenheimer',     'J Robert Oppenheimer portrait physicist atomic bomb Manhattan'),
    33: ('Linus Pauling',   'Linus Pauling portrait chemist molecular biology Nobel'),
    34: ('Francis Crick',   'Francis Crick portrait photograph DNA double helix'),
    35: ('James Watson',    'James Watson portrait photograph DNA biologist'),
    36: ('Hawking',         'Stephen Hawking wheelchair portrait physicist Cambridge'),
}

LISTS['grandes_explorations'] = {
    1:  ('Christophe Colomb',   'Christopher Columbus portrait painting Americas explorer'),
    2:  ('Vasco de Gama',       'Vasco da Gama portrait painting Portuguese explorer India'),
    3:  ('Magellan',            'Ferdinand Magellan portrait painting circumnavigation'),
    4:  ('Amerigo Vespucci',    'Amerigo Vespucci portrait painting explorer Americas'),
    5:  ('John Cabot',          'John Cabot explorer portrait painting England'),
    6:  ('Francis Drake',       'Francis Drake portrait circumnavigation England pirate'),
    7:  ('Henry Hudson',        'Henry Hudson explorer portrait painting river bay'),
    8:  ('Abel Tasman',         'Abel Tasman explorer portrait Australia New Zealand'),
    9:  ('James Cook',          'James Cook portrait painting explorer Pacific'),
    10: ('Humboldt',            'Alexander von Humboldt portrait naturalist explorer'),
    11: ('Lewis et Clark',      'Lewis Clark expedition America map portrait'),
    12: ('Jacques Cartier',     'Jacques Cartier portrait painting explorer Canada'),
    13: ('Samuel de Champlain', 'Samuel de Champlain portrait painting explorer Canada'),
    14: ('La Salle',            'René-Robert Cavelier La Salle explorer Mississippi portrait'),
    15: ('Henri le Navigateur', 'Henry the Navigator Portugal portrait explorer caravel'),
    16: ('David Livingstone',   'David Livingstone portrait explorer Africa missionary'),
    17: ('Mungo Park',          'Mungo Park portrait explorer Africa Niger River'),
    18: ('Amundsen',            'Roald Amundsen portrait South Pole Antarctic explorer'),
    19: ('Shackleton',          'Ernest Shackleton Endurance Antarctica portrait explorer'),
    20: ('Robert Scott',        'Robert Falcon Scott Antarctica portrait photograph'),
    21: ('Edmund Hillary',      'Edmund Hillary Everest summit 1953 portrait mountaineer'),
    22: ('Youri Gagarine',      'Yuri Gagarin cosmonaut Soviet space suit portrait'),
    23: ('Neil Armstrong',      'Neil Armstrong astronaut Moon Apollo 11 portrait'),
    24: ('Valentina Terechkova','Valentina Tereshkova cosmonaut Soviet portrait first woman'),
    25: ('Buzz Aldrin',         'Buzz Aldrin astronaut Moon Apollo 11 spacesuit portrait'),
}

LISTS['inventions_majeures'] = {
    1:  ('La roue',             'ancient wheel Mesopotamia pottery clay history'),
    2:  ("L'écriture",          'cuneiform writing Mesopotamia clay tablet ancient Sumerian'),
    3:  ('Imprimerie',          'Gutenberg printing press movable type 1450 invention'),
    4:  ('Machine à vapeur',    'Watt steam engine industrial revolution Newcomen'),
    5:  ('Téléphone',           'Alexander Graham Bell telephone 1876 patent portrait'),
    6:  ('Ampoule électrique',  'Thomas Edison incandescent light bulb filament laboratory'),
    7:  ('Automobile',          'Benz Patent-Motorwagen 1885 first automobile three-wheel'),
    8:  ('Avion',               'Wright brothers Flyer Kitty Hawk 1903 first flight'),
    9:  ('Télévision',          'John Logie Baird television 1926 invention early screen'),
    10: ('Pénicilline',         'Alexander Fleming penicillin Petri dish antibiotic mold'),
    11: ('Ordinateur',          'ENIAC computer 1945 vacuum tubes enormous room'),
    12: ('Internet',            'ARPANET network diagram nodes 1969 internet history'),
    13: ('Transistor',          'transistor Bell Labs 1947 semiconductor Shockley invention'),
    14: ('Laser',               'Theodore Maiman laser 1960 ruby red beam invention'),
    15: ('Plastique',           'Bakelite plastic invention Baekeland 1907 polymer'),
    16: ('Réacteur nucléaire',  'Chicago Pile-1 first nuclear reactor 1942 Fermi'),
    17: ('Satellite',           'Sputnik 1957 Soviet satellite space orbit sphere'),
    18: ('Circuit intégré',     'integrated circuit silicon chip Intel microprocessor'),
    19: ('World Wide Web',      'Tim Berners-Lee World Wide Web CERN proposal 1989'),
    20: ('Smartphone',          'Apple iPhone 2007 Steve Jobs keynote first announcement'),
    21: ('GPS',                 'GPS satellite constellation global positioning navigation'),
    22: ('Impression 3D',       '3D printing additive manufacturing FDM prototype layer'),
    23: ('Poudre à canon',      'gunpowder Chinese invention medieval cannon fireworks'),
    24: ('Boussole',            'magnetic compass Chinese invention navigation ship'),
    25: ('Horloge mécanique',   'mechanical clock tower medieval escapement invention'),
    26: ('Télescope',           'Galileo telescope invention 1609 astronomy refractor'),
    27: ('Microscope',          'Leeuwenhoek microscope invention bacteria 17th century'),
    28: ('Vaccination',         'Edward Jenner smallpox vaccination cowpox 1796'),
    29: ('Chemin de fer',       "Stephenson Rocket locomotive 1829 Rainhill first railway"),
    30: ('Radio',               'Marconi radio telegraph wireless transmission 1895 patent'),
}

LISTS['civilisations'] = {
    1:  ("Égypte antique",      'ancient Egypt Giza pyramids Sphinx aerial photo'),
    2:  ('Mésopotamie',         'Mesopotamia Babylon ruins Ishtar Gate Iraq ancient'),
    3:  ('Grèce antique',       'ancient Greece Parthenon Acropolis Athens aerial'),
    4:  ('Empire romain',       'Roman Empire Colosseum Rome aerial ruins'),
    5:  ('Empire perse',        'Persian Empire Persepolis ruins Apadana staircase Iran'),
    6:  ('Chine ancienne',      'ancient China Great Wall aerial Badaling photo'),
    7:  ('Civilisation indus',  'Indus Valley civilization Mohenjo-daro Harappa ruins'),
    8:  ('Mayas',               'Maya civilization Chichen Itza pyramid El Castillo'),
    9:  ('Aztèques',            'Aztec Tenochtitlan reconstruction pyramid Temple Mayor'),
    10: ('Incas',               'Inca Machu Picchu aerial Peru ruins Andes'),
    11: ('Empire byzantin',     'Byzantine Hagia Sophia Constantinople mosaic Emperor'),
    12: ("Âge d'or islamique",  'Islamic Golden Age manuscript astronomy Baghdad Al-Biruni'),
    13: ('Vikings',             'Viking longship Drakkar Oseberg museum Norway'),
    14: ('Saint-Empire',        'Holy Roman Empire Cologne Cathedral medieval map'),
    15: ('Empire mongol',       'Mongol Empire horseback cavalry steppe map expansion'),
    16: ('Empire ottoman',      'Ottoman Empire Suleiman Magnificent Topkapi Constantinople'),
    17: ('Empire moghol',       'Mughal Empire Taj Mahal Agra marble aerial'),
    18: ('Empire britannique',  'British Empire map 1897 colonial Victorian world'),
    19: ('Empire carolingien',  'Charlemagne Carolingian Empire map medieval illustration'),
    20: ('Carthage',            'ancient Carthage ruins Tunisia Punic Antonine Baths'),
    21: ('Civilisation minoenne','Minoan Knossos Crete fresco bull leaping palace'),
    22: ('Phénicie',            'Phoenician ship purple dye trade Mediterranean ancient'),
    23: ('Hittites',            'Hittite Hattusa ruins Turkey Anatolian ancient stone'),
    24: ('Nubie',               'Nubian pyramids Meroe Sudan aerial Africa ancient'),
    25: ('Empire achéménide',   'Achaemenid Persian Persepolis relief frieze soldiers'),
}

LISTS['guerres'] = {
    1:  ('Guerre de Troie',     'Trojan War wooden horse Troy ancient Greek vase painting'),
    2:  ('Guerres médiques',    'Battle of Marathon Salamis ancient Greek trireme painting'),
    3:  ('Guerre du Péloponnèse','Peloponnesian War Athens Sparta ancient map Thucydides'),
    4:  ('Guerres puniques',    'Punic Wars Hannibal elephants Alps Roman legion painting'),
    5:  ('Guerres des Gaules',  'Julius Caesar Gallic Wars battle legions painting'),
    6:  ('Guerre de Cent Ans',  'Hundred Years War Joan of Arc French English medieval painting'),
    7:  ('Croisades',           'Crusades Jerusalem medieval siege knights painting'),
    8:  ('Invasions mongoles',  'Mongol invasion Genghis Khan cavalry destruction medieval'),
    9:  ('Guerres ottomanes',   'Ottoman conquest Constantinople 1453 siege Mehmed II'),
    10: ('Guerre de Trente Ans','Thirty Years War 1618 Westphalia Europe devastation'),
    11: ('Révolution américaine','American Revolutionary War Battle Bunker Hill painting'),
    12: ('Guerres napoléoniennes','Napoleonic Wars Waterloo 1815 painting battle'),
    13: ('Guerre de Crimée',    'Crimean War 1854 Charge Light Brigade Balaclava photo'),
    14: ('Guerre de Sécession', 'American Civil War Gettysburg 1863 soldiers photograph'),
    15: ('Guerre franco-prussienne','Franco-Prussian War 1870 Sedan Napoleon III surrender'),
    16: ('Première Guerre mondiale','World War I Western Front trenches soldiers photo'),
    17: ('Deuxième Guerre mondiale','World War II D-Day Omaha Beach Normandy 1944 photo'),
    18: ('Guerre de Corée',     'Korean War 1950 soldiers Inchon landing battle photo'),
    19: ('Guerre du Viêt Nam',  'Vietnam War soldiers jungle battle photograph Ap Bac'),
    20: ('Guerre du Golfe',     'Gulf War 1991 coalition soldiers M1A1 tank desert photo'),
    21: ('Afghanistan',         'Afghanistan War 2001 soldiers mountains Kandahar photo'),
    22: ("Guerre d'Irak",       'Iraq War 2003 Baghdad soldiers urban combat photograph'),
}

LISTS['rois_france'] = {
    1:  ('Clovis Ier',          'Clovis I baptism Rheims Frankish king mosaic medieval'),
    2:  ('Dagobert Ier',        'Dagobert I Frankish king golden portrait medieval'),
    3:  ('Pépin le Bref',       'Pepin the Short Carolingian Frankish king portrait'),
    4:  ('Charlemagne',         'Charlemagne emperor portrait painting Albrecht Dürer'),
    5:  ('Louis le Pieux',      'Louis the Pious Carolingian portrait medieval'),
    6:  ('Charles le Chauve',   'Charles the Bald medieval illuminated portrait'),
    7:  ('Hugues Capet',        'Hugh Capet Capetian dynasty founder king portrait'),
    8:  ('Robert II',           'Robert II Pious Capetian king France medieval'),
    9:  ('Philippe Ier',        'Philip I Capetian king France medieval portrait'),
    10: ('Louis VI',            'Louis VI Fat king France medieval portrait'),
    11: ('Louis VII',           'Louis VII France Crusades king medieval portrait'),
    12: ('Philippe II Auguste', 'Philip II Augustus France medieval portrait Crusade'),
    13: ('Louis VIII',          'Louis VIII France medieval king Capetian portrait'),
    14: ('Saint Louis IX',      'Saint Louis IX king France medieval crusades portrait Joinville'),
    15: ('Philippe III',        'Philip III Bold France medieval Capetian portrait'),
    16: ('Philippe IV le Bel',  'Philip IV Fair France medieval portrait Templars'),
    17: ('Louis X',             'Louis X Hutin France medieval Capetian king'),
    18: ('Philippe V',          'Philip V Long France medieval Capetian portrait'),
    19: ('Charles IV',          'Charles IV Fair France medieval Capetian king'),
    20: ('Philippe VI',         'Philip VI Valois France medieval portrait king'),
    21: ('Jean II le Bon',      'Jean II Good France medieval portrait Louvre painting'),
    22: ('Charles V le Sage',   'Charles V Wise France medieval portrait'),
    23: ('Charles VI le Fou',   'Charles VI Mad France medieval portrait'),
    24: ('Charles VII',         'Charles VII France medieval portrait Joan of Arc'),
    25: ('Louis XI',            'Louis XI Spider King France medieval portrait'),
    26: ('Charles VIII',        'Charles VIII France medieval portrait Italian Wars'),
    27: ('Louis XII',           'Louis XII Father People France portrait painting'),
    28: ('François Ier',        'Francis I France Renaissance portrait Holbein Clouet painting'),
    29: ('Henri II',            'Henry II France Renaissance portrait painting'),
    30: ('François II',         'Francis II France Valois portrait Mary Stuart'),
    31: ('Charles IX',          'Charles IX France Valois portrait painting'),
    32: ('Henri III',           'Henry III France Valois portrait painting'),
    33: ('Henri IV',            'Henry IV France Bourbon Navarre portrait painting'),
    34: ('Louis XIII',          'Louis XIII France Bourbon portrait painting Philippe de Champaigne'),
    35: ('Louis XIV',           'Louis XIV Sun King portrait Hyacinthe Rigaud painting 1701'),
    36: ('Louis XV',            'Louis XV France portrait painting Quentin de La Tour'),
    37: ('Louis XVI',           'Louis XVI France portrait painting Callet'),
    38: ('Napoléon Bonaparte',  'Napoleon I Emperor France portrait David painting'),
    39: ('Louis XVIII',         'Louis XVIII France Bourbon restoration portrait painting'),
    40: ('Charles X',           'Charles X France Bourbon portrait painting'),
    41: ('Louis-Philippe',      'Louis-Philippe July Monarchy France portrait painting'),
}

LISTS['mythologie'] = {
    1:  ('Zeus',        'Zeus king gods ancient Greek sculpture Otricoli marble'),
    2:  ('Héra',        'Hera Greek goddess queen ancient sculpture marble'),
    3:  ('Poséidon',    'Poseidon god sea trident ancient Greek bronze sculpture'),
    4:  ('Déméter',     'Demeter Greek goddess harvest grain ancient vase painting'),
    5:  ('Athéna',      'Athena Parthenon goddess helmet spear ancient Greek'),
    6:  ('Apollon',     'Apollo Belvedere Greek god sun ancient Roman marble sculpture'),
    7:  ('Artémis',     'Artemis Greek goddess hunt arrow ancient marble sculpture'),
    8:  ('Arès',        'Ares Greek god war ancient Roman marble sculpture'),
    9:  ('Aphrodite',   'Aphrodite de Milo Venus Greek goddess love marble Louvre'),
    10: ('Héphaïstos',  'Hephaestus blacksmith forge Greek vase painting fire'),
    11: ('Hermès',      'Hermes messenger Greek god winged helmet Lysippos bronze'),
    12: ('Dionysos',    'Dionysus Bacchus Greek god wine ancient vase painting ivy'),
    13: ('Hadès',       'Hades Persephone abduction Greek vase underworld painting'),
    14: ('Perséphone',  'Persephone Greek goddess spring pomegranate ancient vase'),
    15: ('Hestia',      'Hestia Vesta Greek goddess hearth flame ancient sculpture'),
    16: ('Nyx',         'Nyx Greek goddess night ancient pottery black figure'),
    17: ('Cronos',      'Cronus Saturn devouring child Goya Francisco painting'),
    18: ('Hécate',      'Hecate Greek goddess magic torches triple moon'),
    19: ('Prométhée',   'Prometheus fire eagle Rubens painting chained cliff'),
    20: ('Atlas',       'Atlas Titan globe Farnese ancient Roman marble sculpture'),
    21: ('Héraclès',    'Heracles Hercules Farnese ancient sculpture lion skin'),
    22: ('Achille',     'Achilles Troy warrior ancient Greek vase armor red figure'),
    23: ('Ulysse',      'Odysseus Ulysses ancient Greek vase black figure Troy'),
    24: ('Thésée',      'Theseus Minotaur ancient Greek vase labyrinth Athens'),
    25: ('Méduse',      'Medusa Gorgon Perseus ancient Greek vase marble rondanini'),
    26: ('Persée',      'Perseus Medusa head Cellini bronze sculpture Florence'),
    27: ('Orphée',      'Orpheus Eurydice lyre ancient Greek marble painting'),
    28: ('Sisyphe',     'Sisyphus boulder Titian painting ancient myth'),
    29: ('Narcisse',    'Narcissus water reflection Caravaggio painting'),
    30: ('Œdipe',       'Oedipus Sphinx Ingres painting answer riddle'),
    31: ('Pandore',     'Pandora box Waterhouse painting Pre-Raphaelite'),
    32: ('Jason',       'Jason Argonauts Golden Fleece Herbert Draper painting'),
    33: ('Médée',       'Medea Jason Delacroix painting flying dragon chariot'),
    34: ('Icare',       'Icarus wax wings sun fall Rubens Bruegel painting'),
    35: ('Cerbère',     'Cerberus three headed dog Hades Flaxman engraving'),
}

LISTS['litterature'] = {
    1:  ('Iliade',              'Iliad Achilles Troy ancient Greek vase painting red figure'),
    2:  ('Odyssée',             'Odyssey Ulysses Cyclops ship ancient Greek vase painting'),
    3:  ('Divine Comédie',      'Dante Divine Comedy Doré engraving Inferno illustration'),
    4:  ('Don Quichotte',       'Don Quixote Cervantes windmills Doré illustration 1863'),
    5:  ('William Shakespeare', 'William Shakespeare portrait Chandos painting Globe Theatre'),
    6:  ('Hamlet',              'Hamlet Ophelia Millais painting Pre-Raphaelite water flowers'),
    7:  ('Candide',             'Voltaire Candide philosophical tale illustration 18th century'),
    8:  ('Les Misérables',      'Victor Hugo Les Misérables Cosette Émile Bayard illustration'),
    9:  ('Madame Bovary',       'Flaubert Madame Bovary French novel 1857 illustration'),
    10: ('Crime et Châtiment',  'Dostoevsky Crime Punishment Russian novel illustration'),
    11: ('Guerre et Paix',      'Tolstoy War Peace Borodino battle illustration'),
    12: ('Anna Karénine',       'Tolstoy Anna Karenina railway station illustration'),
    13: ('Moby Dick',           'Melville Moby Dick white whale ship Nantucket illustration'),
    14: ('Dorian Gray',         'Wilde Picture Dorian Gray portrait Victorian painting'),
    15: ('À la Recherche',      'Proust Remembrance Things Past madeleine tea cup'),
    16: ('Ulysse',              'James Joyce Ulysses Dublin portrait photograph'),
    17: ('Gatsby le Magnifique','Great Gatsby Fitzgerald 1920s Jazz Age party roaring'),
    18: ("L'Étranger",          'Camus The Stranger Absurd Meursault Algeria sun beach'),
    19: ('Le Procès',           'Kafka Trial Josef K bureaucracy surreal'),
    20: ('Faust',               'Goethe Faust Mephistopheles devil deal Delacroix painting'),
    21: ('La Ferme des animaux','Animal Farm Orwell pig trough totalitarianism illustrated'),
    22: ('1984',                'Orwell 1984 Big Brother telescreen poster dystopia'),
    23: ('Seigneur des Anneaux','Tolkien Lord of the Rings Shire Rivendell illustration'),
    24: ('Cent ans de Solitude','García Márquez Hundred Years Solitude Macondo cover'),
    25: ('Dune',                'Frank Herbert Dune Arrakis desert sandworm science fiction'),
    26: ('Harry Potter',        'Harry Potter Hogwarts castle lightning bolt wizard'),
    27: ('Les Fleurs du Mal',   'Baudelaire Flowers Evil Paris symbolism poetry portrait'),
    28: ('À la recherche 2',    'Proust cork-lined bedroom Illiers-Combray photograph'),
}

LISTS['batailles_decisives'] = {
    1:  ('Marathon',            'Battle of Marathon 490 BC ancient Greek Persian illustration'),
    2:  ('Hastings',            'Battle of Hastings 1066 Bayeux Tapestry Norman conquest'),
    3:  ('Bouvines',            'Battle of Bouvines 1214 France Philip Augustus medieval painting'),
    4:  ('Waterloo',            'Battle of Waterloo 1815 Napoleon Wellington painting'),
    5:  ('Verdun',              'Battle of Verdun 1916 World War I trenches soldiers'),
    6:  ('Stalingrad',          'Battle of Stalingrad 1942 Soviet Red Army ruins rubble'),
    7:  ('Midway',              'Battle of Midway 1942 aircraft carrier explosion Pacific'),
    8:  ('Gaugamèles',          'Battle of Gaugamela Alexander Great Darius mosaic Pompeii'),
    9:  ('Cannes',              'Battle of Cannae 216 BC Hannibal Roman encirclement diagram'),
    10: ('Actium',              'Battle of Actium 31 BC Augustus Cleopatra naval painting'),
    11: ('Poitiers',            'Battle of Tours Poitiers 732 Charles Martel Arabic'),
    12: ('Lépante',             'Battle of Lepanto 1571 Christian Ottoman naval painting'),
    13: ('Austerlitz',          'Battle of Austerlitz 1805 Napoleon three emperors painting'),
    14: ('Marne',               'First Battle of Marne 1914 French soldiers taxi German'),
    15: ('Somme',               'Battle of Somme 1916 British soldiers mud trench WWI'),
    16: ('El-Alamein',          'Second Battle El Alamein 1942 Montgomery Rommel desert'),
    17: ('Koursk',              'Battle of Kursk 1943 Soviet tank T-34 German Tiger Eastern Front'),
    18: ('Normandie',           'D-Day Normandy landing 1944 Omaha Beach soldiers coast'),
    19: ('Berlin 1945',         'Battle of Berlin 1945 Soviet soldiers Reichstag flag'),
    20: ('Diên Biên Phu',       'Battle Dien Bien Phu 1954 French Viet Minh soldiers'),
}

LISTS['fleuves_monde'] = {
    1:  ('Nil',         'Nile River Egypt aerial satellite photo green valley'),
    2:  ('Amazone',     'Amazon River Brazil aerial rainforest meandering'),
    3:  ('Yangtsé',     'Yangtze River China Three Gorges Dam aerial'),
    4:  ('Mississippi', 'Mississippi River USA aerial meander delta bayou'),
    5:  ('Ienisseï',    'Yenisei River Siberia Russia aerial landscape'),
    6:  ('Fleuve Jaune','Yellow River China Huang He loess plateau aerial'),
    7:  ('Ob',          'Ob River Siberia Russia aerial landscape map'),
    8:  ('Paraná',      'Paraná River South America aerial delta Argentina'),
    9:  ('Congo',       'Congo River Africa aerial rainforest basin'),
    10: ('Amour',       'Amur River Russia China aerial landscape Manchuria'),
    11: ('Léna',        'Lena River Siberia Russia delta aerial NASA photo'),
    12: ('Mékong',      'Mekong River Southeast Asia aerial delta Vietnam'),
    13: ('Niger',       'Niger River Africa aerial Mali landscape Bamako'),
    14: ('Mackenzie',   'Mackenzie River Canada Northwest Territories delta Arctic'),
    15: ('Volga',       'Volga River Russia longest Europe aerial landscape'),
    16: ('Zambèze',     'Zambezi River Victoria Falls aerial Zambia Zimbabwe'),
    17: ('Orénoque',    'Orinoco River Venezuela aerial jungle delta map'),
    18: ('Euphrate',    'Euphrates River Iraq Syria Mesopotamia aerial'),
    19: ('Tigre',       'Tigris River Iraq Mosul Mesopotamia aerial'),
    20: ('Gange',       'Ganges River India Varanasi ghats aerial holy Hindu'),
    21: ('Indus',       'Indus River Pakistan India aerial Himalaya delta'),
    22: ('Murray',      'Murray River Australia aerial South Australia'),
    23: ('Danube',      'Danube River Budapest Iron Gate aerial Europe'),
    24: ('Saint-Laurent','Saint Lawrence River Canada Quebec City aerial'),
    25: ('Colorado',    'Colorado River Grand Canyon aerial USA'),
    26: ('Rio Grande',  'Rio Grande River USA Mexico border aerial desert'),
    27: ('Orange',      'Orange River South Africa Lesotho aerial landscape'),
    28: ('Rhin',        'Rhine River Europe Loreley aerial Germany Switzerland'),
    29: ('Sénégal',     'Senegal River West Africa aerial Dakar delta'),
    30: ('Irrawaddy',   'Irrawaddy River Myanmar Burma aerial delta'),
}

LISTS['constellations'] = {
    1:  ('Orion',               'Orion constellation stars Rigel Betelgeuse nebula photo'),
    2:  ('Grande Ourse',        'Ursa Major Big Dipper constellation star trail long exposure'),
    3:  ('Petite Ourse',        'Ursa Minor Little Dipper Polaris North Star constellation'),
    4:  ('Cassiopée',           'Cassiopeia W constellation Milky Way stars photo'),
    5:  ('Scorpion',            'Scorpius constellation Antares Milky Way stars astrophoto'),
    6:  ('Lion',                'Leo constellation Regulus lion stars night sky'),
    7:  ('Vierge',              'Virgo constellation Spica galaxy cluster stars'),
    8:  ('Gémeaux',             'Gemini constellation Castor Pollux twin stars'),
    9:  ('Verseau',             'Aquarius constellation water bearer stars nebula'),
    10: ('Poissons',            'Pisces fish constellation stars night sky'),
    11: ('Bélier',              'Aries ram constellation stars night sky'),
    12: ('Taureau',             'Taurus Pleiades Hyades bull constellation stars'),
    13: ('Cancer',              'Cancer crab constellation Beehive Praesepe cluster'),
    14: ('Balance',             'Libra scales constellation stars night sky'),
    15: ('Sagittaire',          'Sagittarius teapot Milky Way core constellation stars'),
    16: ('Capricorne',          'Capricornus sea goat constellation stars night sky'),
    17: ('Persée',              'Perseus constellation Algol double cluster stars'),
    18: ('Andromède',           'Andromeda galaxy M31 constellation night sky photo'),
    19: ('Cygne',               'Cygnus swan Northern Cross Deneb Milky Way constellation'),
    20: ('Lyre',                'Lyra constellation Vega Ring Nebula M57 stars photo'),
    21: ('Aigle',               'Aquila eagle Altair constellation Milky Way stars'),
    22: ('Hercule',             'Hercules constellation M13 globular cluster stars'),
    23: ('Bouvier',             'Boötes constellation Arcturus orange star night sky'),
    24: ('Dragon',              'Draco dragon constellation circumpolar stars night'),
    25: ('Centaure',            'Centaurus Alpha Centauri closest star southern sky'),
    26: ('Croix du Sud',        'Southern Cross Crux constellation southern hemisphere'),
    27: ('Grand Chien',         'Canis Major Sirius brightest star constellation night'),
    28: ('Petit Chien',         'Canis Minor Procyon constellation stars night sky'),
    29: ('Hydre',               'Hydra constellation largest stars night sky'),
    30: ('Orion nébuleuse',     'Orion Nebula M42 stellar nursery Hubble photo'),
}

LISTS['detroits_monde'] = {
    1:  ('Gibraltar',       'Strait of Gibraltar aerial Spain Morocco Mediterranean Atlantic'),
    2:  ('Bosphore',        'Bosphorus Istanbul Turkey aerial bridge suspension strait'),
    3:  ('Dardanelles',     'Dardanelles Çanakkale Turkey strait aerial'),
    4:  ('Hormuz',          'Strait of Hormuz aerial oil tanker Gulf Oman Iran'),
    5:  ('Malacca',         'Strait of Malacca aerial container ship Singapore Malaysia'),
    6:  ('Béring',          'Bering Strait Alaska Russia aerial sea ice satellite'),
    7:  ('Magellan',        'Strait of Magellan Patagonia Chile aerial fjord narrow'),
    8:  ('Bab-el-Mandeb',   'Bab-el-Mandeb strait aerial Yemen Djibouti Red Sea'),
    9:  ('Calais',          'Strait of Dover Channel Tunnel aerial England France'),
    10: ('Messine',         'Strait of Messina Sicily Calabria Italy aerial bridge'),
    11: ('Taiwan',          'Taiwan Strait aerial China island sea satellite'),
    12: ('Corée',           'Korea Strait Japan South Korea Tsushima aerial sea'),
    13: ('Lombok',          'Lombok Strait Indonesia Bali Java aerial satellite'),
    14: ('Floride',         'Florida Straits aerial Cuba USA Miami satellite'),
    15: ('Øresund',         'Øresund strait bridge Copenhague Malmö aerial'),
    16: ('Mozambique',      'Mozambique Channel aerial Madagascar Africa satellite'),
    17: ('Singapour',       'Singapore Strait ship traffic aerial port'),
    18: ('Bass',            'Bass Strait Australia Tasmania aerial sea'),
    19: ('Skagerrak',       'Skagerrak strait Denmark Norway Sweden aerial sea'),
    20: ('Tsugaru',         'Tsugaru Strait Japan Hokkaido Honshu Seikan Tunnel aerial'),
}

LISTS['revolutions'] = {
    1:  ('Révolution américaine',       'American Revolution 1776 Independence Declaration painting Continental'),
    2:  ('Révolution française',        'French Revolution 1789 Bastille storming crowd painting'),
    3:  ('Révolution haïtienne',        'Haitian Revolution Toussaint Louverture portrait independence 1804'),
    4:  ('Indépendances Amérique latine','Simon Bolivar portrait painting South American independence'),
    5:  ('Révolutions 1848',            'Revolutions 1848 barricades Paris Berlin spring nations'),
    6:  ('Restauration Meiji',          'Meiji Restoration 1868 Japan Emperor modernization Western'),
    7:  ('Révolution russe',            'Russian Revolution October 1917 Bolshevik Lenin soldiers Petrograd'),
    8:  ('Révolution chinoise 1911',    'Xinhai Revolution 1911 Sun Yat-sen Chinese republic Wuhan'),
    9:  ('Révolution mexicaine',        'Mexican Revolution 1910 Zapata Villa portrait photograph'),
    10: ('Indépendance indienne',       'Indian independence Gandhi salt march 1930 Dandi nonviolent'),
    11: ('Révolution chinoise 1949',    'Communist Revolution China 1949 Mao Zedong Tiananmen proclamation'),
    12: ('Révolution cubaine',          'Cuban Revolution Fidel Castro Che Guevara guerrilla Sierra Maestra'),
    13: ('Révolution iranienne',        'Iranian Revolution 1979 Khomeini Tehran protesters street'),
    14: ('Chute du Mur',                'Berlin Wall fall 1989 crowd celebrate hammer checkpoint Charlie'),
    15: ('Révolution de velours',       'Velvet Revolution 1989 Prague Wenceslas Square Havel crowd'),
    16: ('Printemps arabe',             'Arab Spring 2011 Tahrir Square Cairo crowd protest Egypt'),
}

LISTS['chefs_etat'] = {
    1:  ('George Washington',   'George Washington portrait Gilbert Stuart painting President USA'),
    2:  ('Abraham Lincoln',     'Abraham Lincoln portrait photograph Brady President Civil War'),
    3:  ('Napoléon Bonaparte',  'Napoleon Bonaparte Emperor portrait David painting'),
    4:  ('Winston Churchill',   'Winston Churchill portrait photograph cigar WWII'),
    5:  ('Charles de Gaulle',   'Charles de Gaulle portrait photograph France Free French WWII'),
    6:  ('Otto von Bismarck',   'Bismarck Iron Chancellor portrait photograph uniform Prussia'),
    7:  ('Lénine',              'Lenin Vladimir Ulyanov portrait photograph Soviet revolutionary'),
    8:  ('Staline',             'Stalin Joseph portrait photograph Soviet leader'),
    9:  ('Hitler',              'Adolf Hitler portrait photograph Nazi Germany'),
    10: ('Mussolini',           'Mussolini Benito portrait photograph fascist Italy Duce'),
    11: ('Franklin Roosevelt',  'Franklin D Roosevelt portrait photograph New Deal USA president'),
    12: ('Mao Zedong',          'Mao Zedong portrait Communist China photograph'),
    13: ('Gandhi',              'Mahatma Gandhi portrait photograph round glasses independence India'),
    14: ('Nelson Mandela',      'Nelson Mandela portrait photograph Robben Island South Africa'),
    15: ('John F Kennedy',      'John F Kennedy JFK portrait photograph President White House'),
    16: ('Fidel Castro',        'Fidel Castro portrait photograph military beard Cuba'),
    17: ('Che Guevara',         'Che Guevara iconic portrait Korda photograph beret'),
    18: ('Hô Chi Minh',         'Ho Chi Minh portrait photograph North Vietnam leader'),
    19: ('Jawaharlal Nehru',    'Nehru portrait photograph India prime minister independence'),
    20: ('Simón Bolívar',       'Simón Bolívar portrait painting South American liberator'),
    21: ('Mustafa Kemal Atatürk','Kemal Atatürk portrait photograph Turkey founder modern'),
    22: ('Franklin Roosevelt 2','FDR Roosevelt wheelchair Warm Springs portrait photograph'),
    23: ('Harry Truman',        'Harry Truman portrait photograph atomic bomb president USA'),
    24: ('Dwight Eisenhower',   'Eisenhower portrait photograph president general WWII'),
    25: ('Margaret Thatcher',   'Margaret Thatcher portrait photograph Iron Lady UK prime minister'),
}

LISTS['jo_ete'] = {
    1:  ('Athènes 1896',    'Athens 1896 Summer Olympics first modern Games stadium Panathenaic'),
    2:  ('Paris 1900',      'Paris 1900 Summer Olympics exposition universelle'),
    3:  ('Saint-Louis 1904','St Louis 1904 Summer Olympics World Fair USA'),
    4:  ('Londres 1908',    'London 1908 Summer Olympics White City stadium marathon'),
    5:  ('Stockholm 1912',  'Stockholm 1912 Summer Olympics Sweden opening ceremony'),
    6:  ('Anvers 1920',     'Antwerp 1920 Summer Olympics Belgium athletes flag'),
    7:  ('Paris 1924',      'Paris 1924 Summer Olympics Colombes stadium Chariots of Fire'),
    8:  ('Amsterdam 1928',  'Amsterdam 1928 Summer Olympics Netherlands flame torch'),
    9:  ('Los Angeles 1932','Los Angeles 1932 Summer Olympics Coliseum athletes'),
    10: ('Berlin 1936',     'Berlin 1936 Summer Olympics Jesse Owens Nazi stadium'),
    11: ('Londres 1948',    'London 1948 Summer Olympics Wembley postwar austerity'),
    12: ('Helsinki 1952',   'Helsinki 1952 Summer Olympics Finland Paavo Nurmi torch'),
    13: ('Melbourne 1956',  'Melbourne 1956 Summer Olympics Australia athletes rowing'),
    14: ('Rome 1960',       'Rome 1960 Summer Olympics Abebe Bikila marathon barefoot'),
    15: ('Tokyo 1964',      'Tokyo 1964 Summer Olympics Japan opening ceremony national stadium'),
    16: ('Mexico 1968',     'Mexico City 1968 Olympics Black Power salute altitude'),
    17: ('Munich 1972',     'Munich 1972 Olympics Germany terror attack memorial'),
    18: ('Montréal 1976',   'Montreal 1976 Summer Olympics Canada stadium Nadia Comaneci'),
    19: ('Moscou 1980',     'Moscow 1980 Summer Olympics Soviet Union Misha bear mascot'),
    20: ('Los Angeles 1984','Los Angeles 1984 Olympics Carl Lewis sprint USA gold'),
    21: ('Séoul 1988',      'Seoul 1988 Summer Olympics Korea opening ceremony dragon'),
    22: ('Barcelone 1992',  'Barcelona 1992 Summer Olympics Spain Montjuïc stadium'),
    23: ('Atlanta 1996',    'Atlanta 1996 Summer Olympics centennial Coke bottle Centennial Park'),
    24: ('Sydney 2000',     'Sydney 2000 Summer Olympics Opera House Cathy Freeman torch'),
    25: ('Athènes 2004',    'Athens 2004 Summer Olympics Panathenaic return Greece'),
    26: ('Pékin 2008',      'Beijing 2008 Summer Olympics Birds Nest stadium fireworks'),
    27: ('Londres 2012',    'London 2012 Summer Olympics opening ceremony Queen Bond'),
    28: ('Rio 2016',        'Rio 2016 Summer Olympics Maracanã torch Christ Redeemer'),
    29: ('Tokyo 2020',      'Tokyo 2021 Summer Olympics Japan pandemic empty stadium'),
    30: ('Paris 2024',      'Paris 2024 Summer Olympics Seine River ceremony Eiffel Tower'),
    31: ('Los Angeles 2028','Los Angeles 2028 Summer Olympics announcement'),
}

LISTS['jo_hiver'] = {
    1:  ('Chamonix 1924',   'Chamonix 1924 Winter Olympics first alpine skiing France'),
    2:  ('Saint-Moritz 1928','Saint Moritz 1928 Winter Olympics Switzerland bobsled'),
    3:  ('Lake Placid 1932','Lake Placid 1932 Winter Olympics USA ice speed skating'),
    4:  ('Garmisch 1936',   'Garmisch-Partenkirchen 1936 Winter Olympics Germany ski'),
    5:  ('Saint-Moritz 1948','Saint Moritz 1948 Winter Olympics postwar return'),
    6:  ('Oslo 1952',       'Oslo 1952 Winter Olympics Norway Holmenkollen ski'),
    7:  ('Cortina 1956',    "Cortina d'Ampezzo 1956 Winter Olympics Italy Dolomites"),
    8:  ('Squaw Valley 1960','Squaw Valley 1960 Winter Olympics California USA ice'),
    9:  ('Innsbruck 1964',  'Innsbruck 1964 Winter Olympics Austria alpine skiing'),
    10: ('Grenoble 1968',   'Grenoble 1968 Winter Olympics France Jean-Claude Killy ski'),
    11: ('Sapporo 1972',    'Sapporo 1972 Winter Olympics Japan Hokkaido ski jump'),
    12: ('Innsbruck 1976',  'Innsbruck 1976 Winter Olympics Austria biathlon'),
    13: ('Lake Placid 1980','Lake Placid 1980 Miracle on Ice USA hockey Soviet Union'),
    14: ('Sarajevo 1984',   'Sarajevo 1984 Winter Olympics Yugoslavia Jahorina ski'),
    15: ('Calgary 1988',    'Calgary 1988 Winter Olympics Canada Jamaica bobsled'),
    16: ('Albertville 1992','Albertville 1992 Winter Olympics France Alps Savoie'),
    17: ('Lillehammer 1994','Lillehammer 1994 Winter Olympics Norway Torvill Dean flame'),
    18: ('Nagano 1998',     'Nagano 1998 Winter Olympics Japan ski jump Masahiko'),
    19: ('Salt Lake City 2002','Salt Lake City 2002 Winter Olympics USA skating'),
    20: ('Turin 2006',      'Turin 2006 Winter Olympics Italy Torino flame ceremony'),
    21: ('Vancouver 2010',  'Vancouver 2010 Winter Olympics Canada hockey gold'),
    22: ('Sotchi 2014',     'Sochi 2014 Winter Olympics Russia ceremony Black Sea'),
    23: ('PyeongChang 2018','PyeongChang 2018 Winter Olympics South Korea ceremony drone'),
    24: ('Pékin 2022',      'Beijing 2022 Winter Olympics China snow ceremony'),
    25: ('Milan 2026',      'Milan Cortina 2026 Winter Olympics Italy Alps logo'),
}

LISTS['coupes_monde'] = {
    1:  ('Uruguay 1930',    'Uruguay 1930 World Cup Centenario Stadium Montevideo final'),
    2:  ('Italie 1934',     'Italy 1934 World Cup Mussolini fascist Vittorio Pozzo trophy'),
    3:  ('France 1938',     'France 1938 World Cup Italy champion Jules Rimet trophy'),
    4:  ('Brésil 1950',     'Brazil 1950 World Cup Maracanã crowd Uruguay Ghiggia'),
    5:  ('Suisse 1954',     'Switzerland 1954 World Cup Bern Miracle West Germany Hungary'),
    6:  ('Suède 1958',      'Sweden 1958 World Cup Pelé Brazil champion trophy'),
    7:  ('Chili 1962',      'Chile 1962 World Cup Brazil champion Amarildo Garrincha'),
    8:  ('Angleterre 1966', 'England 1966 World Cup Wembley Bobby Moore Jules Rimet'),
    9:  ('Mexique 1970',    'Mexico 1970 World Cup Pelé Brazil Azteca gold trophy'),
    10: ('Allemagne 1974',  'West Germany 1974 World Cup Cruyff Netherlands Beckenbauer'),
    11: ('Argentine 1978',  'Argentina 1978 World Cup Kempes ticker tape Buenos Aires'),
    12: ('Espagne 1982',    'Spain 1982 World Cup Italy Rossi Paolo Cabrini trophy'),
    13: ('Mexique 1986',    'Mexico 1986 World Cup Maradona Hand of God Azteca'),
    14: ('Italie 1990',     'Italy 1990 World Cup Schillaci Baggio Germany final Rome'),
    15: ('États-Unis 1994', 'USA 1994 World Cup Brazil Italy Baggio penalty final'),
    16: ('France 1998',     'France 1998 World Cup Zidane Brazil Paris Champs-Élysées celebration'),
    17: ('Corée-Japon 2002','South Korea Japan 2002 World Cup Brazil Ronaldo trophy'),
    18: ('Allemagne 2006',  'Germany 2006 World Cup Zidane headbutt Italy final'),
    19: ('Afrique du Sud 2010','South Africa 2010 World Cup vuvuzela Spain Iniesta final'),
    20: ('Brésil 2014',     'Brazil 2014 World Cup Germany 7-1 semifinal Maracanã final'),
    21: ('Russie 2018',     'Russia 2018 World Cup France Mbappé Pogba Croatia Deschamps'),
    22: ('Qatar 2022',      'Qatar 2022 World Cup Argentina Messi trophy Lusail Stadium'),
}

LISTS['f1_champions'] = {
    1:  ('Nino Farina',         'Nino Farina racing driver Formula 1 1950 champion Alfa Romeo'),
    2:  ('Alberto Ascari',      'Alberto Ascari Formula 1 champion Ferrari 1952 racing driver'),
    3:  ('Juan Manuel Fangio',  'Juan Manuel Fangio Formula 1 champion Argentine 1950s racing car'),
    4:  ('Mike Hawthorn',       'Mike Hawthorn Formula 1 champion Ferrari 1958 British bow tie'),
    5:  ('Jack Brabham',        'Jack Brabham Formula 1 champion Cooper Australian racing driver'),
    6:  ('Phil Hill',           'Phil Hill Formula 1 champion Ferrari 1961 American driver'),
    7:  ('Graham Hill',         'Graham Hill Formula 1 champion BRM 1962 British helmet'),
    8:  ('Jim Clark',           'Jim Clark Formula 1 champion Lotus British racing driver 1963'),
    9:  ('John Surtees',        'John Surtees Formula 1 champion Ferrari 1964 British'),
    10: ('Denny Hulme',         'Denny Hulme Formula 1 champion Brabham New Zealand 1967'),
    11: ('Jackie Stewart',      'Jackie Stewart Formula 1 champion Tyrrell Scottish tartan cap'),
    12: ('Emerson Fittipaldi',  'Emerson Fittipaldi Formula 1 champion Brazil Lotus McLaren'),
    13: ('Niki Lauda',          'Niki Lauda Formula 1 champion Ferrari scars comeback'),
    14: ('James Hunt',          'James Hunt Formula 1 champion McLaren 1976 helmet'),
    15: ('Mario Andretti',      'Mario Andretti Formula 1 champion Lotus USA 1978 driver'),
    16: ('Jody Scheckter',      'Jody Scheckter Formula 1 champion Ferrari 1979 South Africa'),
    17: ('Alan Jones',          'Alan Jones Formula 1 champion Williams Australian 1980'),
    18: ('Nelson Piquet',       'Nelson Piquet Formula 1 champion Brazil Brabham Renault Williams'),
    19: ('Keke Rosberg',        'Keke Rosberg Formula 1 champion Williams Finnish 1982'),
    20: ('Alain Prost',         'Alain Prost Formula 1 champion McLaren racing cockpit France'),
    21: ('Ayrton Senna',        'Ayrton Senna Formula 1 champion McLaren Brazil racing helmet'),
    22: ('Nigel Mansell',       'Nigel Mansell Formula 1 champion Williams British 1992'),
    23: ('Michael Schumacher',  'Michael Schumacher Formula 1 champion Ferrari German'),
    24: ('Damon Hill',          'Damon Hill Formula 1 champion Williams British 1996 helmet'),
    25: ('Jacques Villeneuve',  'Jacques Villeneuve Formula 1 champion Williams Canadian 1997'),
    26: ('Mika Häkkinen',       'Mika Häkkinen Formula 1 champion McLaren Finnish silver arrows'),
    27: ('Kimi Räikkönen',      'Kimi Räikkönen Formula 1 champion Ferrari Finnish Iceman 2007'),
    28: ('Fernando Alonso',     'Fernando Alonso Formula 1 champion Renault Spanish 2005'),
    29: ('Jenson Button',       'Jenson Button Formula 1 champion Brawn GP British 2009'),
    30: ('Sebastian Vettel',    'Sebastian Vettel Formula 1 champion Red Bull German'),
    31: ('Lewis Hamilton',      'Lewis Hamilton Formula 1 champion Mercedes British record'),
    32: ('Max Verstappen',      'Max Verstappen Formula 1 champion Red Bull Dutch'),
}

LISTS['consoles'] = {
    1:  ('Magnavox Odyssey',    'Magnavox Odyssey first home video game console 1972 white box'),
    2:  ('Atari 2600',          'Atari 2600 VCS vintage video game console woodgrain joystick'),
    3:  ('Intellivision',       'Mattel Intellivision vintage game console disc controller'),
    4:  ('ColecoVision',        'Coleco ColecoVision vintage game console'),
    5:  ('NES',                 'Nintendo Entertainment System NES Famicom console controller'),
    6:  ('Sega Master System',  'Sega Master System vintage 8-bit console controller'),
    7:  ('TurboGrafx-16',       'TurboGrafx-16 PC Engine NEC Japan vintage console'),
    8:  ('Sega Mega Drive',     'Sega Mega Drive Genesis 16-bit console black controller'),
    9:  ('Super Nintendo',      'Super Nintendo SNES console purple grey controller'),
    10: ('3DO',                 '3DO Interactive Multiplayer Panasonic FZ-1 console 1993'),
    11: ('Sega Saturn',         'Sega Saturn console white CD grey controller 1994'),
    12: ('PlayStation 1',       'Sony PlayStation One PS1 gray console controller 1994'),
    13: ('Nintendo 64',         'Nintendo 64 N64 gray three-prong controller cartridge'),
    14: ('Dreamcast',           'Sega Dreamcast white swirl logo console VMU controller'),
    15: ('PlayStation 2',       'PlayStation 2 PS2 black slim console DVD player'),
    16: ('Xbox original',       'Microsoft Xbox original green X logo console controller'),
    17: ('GameCube',            'Nintendo GameCube purple lunchbox handle console controller'),
    18: ('PSP',                 'Sony PlayStation Portable PSP handheld UMD screen'),
    19: ('Nintendo DS',         'Nintendo DS dual screen clamshell handheld stylus'),
    20: ('Xbox 360',            'Xbox 360 console white green ring of light'),
    21: ('PlayStation 3',       'PlayStation 3 PS3 black glossy Spider-Man font'),
    22: ('Wii',                 'Nintendo Wii white console Wiimote motion remote'),
    23: ('PlayStation Vita',    'PlayStation Vita PS Vita OLED handheld rear touchpad'),
    24: ('Nintendo 3DS',        'Nintendo 3DS clamshell dual screen handheld 3D'),
    25: ('Xbox One',            'Xbox One console black Microsoft launch 2013'),
    26: ('PlayStation 4',       'PlayStation 4 PS4 slim black console DualShock controller'),
    27: ('Nintendo Switch',     'Nintendo Switch hybrid console Joy-Con dock tablet mode'),
    28: ('Xbox Series X',       'Xbox Series X black box console 2020 Microsoft'),
    29: ('PlayStation 5',       'PlayStation 5 PS5 white futuristic console DualSense'),
    30: ('Steam Deck',          'Steam Deck Valve handheld PC gaming device'),
}

LISTS['films'] = {
    1:  ('Metropolis 1927',     'Metropolis 1927 Fritz Lang robot Maria silent film poster'),
    2:  ('Nosferatu 1922',      'Nosferatu 1922 Murnau vampire shadow staircase horror still'),
    3:  ('Cuirassé Potemkine',  'Battleship Potemkin 1925 Eisenstein Odessa steps baby carriage'),
    4:  ('M le Maudit 1931',    'M Fritz Lang 1931 Peter Lorre serial killer chalk M'),
    5:  ('Blanche-Neige 1937',  'Snow White Seven Dwarfs 1937 Disney animation cel still'),
    6:  ('Le Magicien d\'Oz 1939','Wizard of Oz 1939 Dorothy yellow brick road tornado'),
    7:  ('Citizen Kane 1941',   'Citizen Kane 1941 Welles deep focus Rosebud sled'),
    8:  ('Casablanca 1942',     'Casablanca 1942 Bogart Bergman Rick\'s Café still'),
    9:  ('Rome Ville ouverte',  'Rome Open City 1945 Rossellini Italian neorealism still'),
    10: ('Vélo de voleur 1948', 'Bicycle Thieves 1948 De Sica Italian neorealism father son'),
    11: ('Rashomon 1950',       'Rashomon 1950 Kurosawa Japanese forest gate still'),
    12: ('Chantons sous pluie', 'Singin Rain 1952 Gene Kelly umbrella lamp post musical'),
    13: ('Fenêtre sur cour 1954','Rear Window 1954 Hitchcock James Stewart binoculars'),
    14: ('12 hommes en colère', '12 Angry Men 1957 Lumet jury table still'),
    15: ('Sueurs froides 1958', 'Vertigo 1958 Hitchcock Kim Novak spiral'),
    16: ('À bout de souffle 1960','Breathless 1960 Godard Belmondo car Paris New Wave'),
    17: ('Psychose 1960',       'Psycho 1960 Hitchcock shower scene Marion Crane'),
    18: ('Lawrence d\'Arabie',  'Lawrence of Arabia 1962 Peter O\'Toole desert camel epic'),
    19: ('8½ 1963',             '8½ 1963 Fellini Mastroianni Italian film fantasy'),
    20: ('Bon Brute Truand',    'Good Bad Ugly 1966 Leone Eastwood Western duel desert'),
    21: ('2001 Odyssée espace', '2001 Space Odyssey 1968 Kubrick HAL 9000 Bowman'),
    22: ('Le Parrain 1972',     'Godfather 1972 Coppola Brando horse Don Corleone'),
    23: ('Chinatown 1974',      'Chinatown 1974 Polanski Nicholson Faye Dunaway noir'),
    24: ('Taxi Driver 1976',    'Taxi Driver 1976 Scorsese De Niro New York rain night'),
    25: ('Star Wars 1977',      'Star Wars 1977 George Lucas Luke Skywalker Darth Vader poster'),
    26: ('Apocalypse Now 1979', 'Apocalypse Now 1979 Coppola Vietnam helicopter Brando'),
    27: ('Blade Runner 1982',   'Blade Runner 1982 Ridley Scott Harrison Ford neon rain'),
    28: ('E.T. 1982',           'E.T. Extra-Terrestrial 1982 Spielberg bicycle moon silhouette'),
    29: ('Schindler\'s List',   'Schindler\'s List 1993 Spielberg Holocaust black white film'),
    30: ('Pulp Fiction 1994',   'Pulp Fiction 1994 Tarantino Uma Thurman dance contest'),
    31: ('Shawshank Redemption','Shawshank Redemption 1994 Robbins Freeman poster wall'),
    32: ('Toy Story 1995',      'Toy Story 1995 Pixar Woody Buzz Lightyear animation still'),
    33: ('Titanic 1997',        'Titanic 1997 DiCaprio Winslet ship bow Jack Rose still'),
    34: ('Matrix 1999',         'Matrix 1999 Keanu Reeves green code bullet time sunglasses'),
    35: ('Gladiateur 2000',     'Gladiator 2000 Russell Crowe Colosseum arena Rome'),
    36: ('Spirited Away 2001',  'Spirited Away 2001 Miyazaki bathhouse dragon tunnel still'),
    37: ('Seigneur Anneaux 2001','Lord of the Rings Fellowship Ring 2001 Jackson Gandalf Shire'),
    38: ('Cité de Dieu 2002',   'City of God 2002 favela Brazil gang violence slum still'),
    39: ('No Country for Old Men','No Country Old Men 2007 Coen Brothers Bardem cattle gun'),
    40: ('Dark Knight 2008',    'Dark Knight 2008 Nolan Heath Ledger Joker pencil magic trick'),
    41: ('Inception 2010',      'Inception 2010 Nolan DiCaprio folding Paris buildings dream'),
    42: ('Mad Max Fury Road',   'Mad Max Fury Road 2015 Miller war rig desert action'),
    43: ('Parasite 2019',       'Parasite 2019 Bong Joon-ho rain stairs Korean family'),
}

LISTS['lunes'] = {
    1:  ('Io',          'Io moon Jupiter volcanic surface sulfur NASA Voyager Galileo'),
    2:  ('Europe',      'Europa moon Jupiter icy surface cracks NASA Galileo spacecraft'),
    3:  ('Ganymède',    'Ganymede moon Jupiter largest NASA Galileo surface photo'),
    4:  ('Callisto',    'Callisto moon Jupiter cratered dark surface NASA Galileo'),
    5:  ('Titan',       'Titan moon Saturn Cassini atmosphere haze NASA orange'),
    6:  ('Encelade',    'Enceladus moon Saturn water geysers plumes Cassini NASA'),
    7:  ('Mimas',       'Mimas moon Saturn Death Star crater Herschel Cassini NASA'),
    8:  ('Rhéa',        'Rhea moon Saturn icy surface Cassini NASA'),
    9:  ('Japet',       'Iapetus moon Saturn two-tone dark bright ridge Cassini'),
    10: ('Triton',      'Triton moon Neptune nitrogen geysers Voyager 2 NASA photo'),
    11: ('Charon',      'Charon Pluto binary system New Horizons NASA 2015 photo'),
    12: ('Miranda',     'Miranda moon Uranus cliffs Verona Rupes Voyager 2 NASA'),
    13: ('Titania',     'Titania moon Uranus largest Voyager 2 NASA craters'),
    14: ('Oberon',      'Oberon moon Uranus outermost large Voyager 2 NASA'),
    15: ('Phobos',      'Phobos moon Mars NASA photo groove crater irregular'),
    16: ('Déimos',      'Deimos moon Mars NASA photo small irregular gray'),
    17: ('Lune',        'Moon full resolution NASA LROC detailed surface craters'),
    18: ('Dioné',       'Dione moon Saturn cliffs ice Cassini NASA photo'),
    19: ('Téthys',      'Tethys moon Saturn Odysseus crater Cassini NASA'),
    20: ('Hypérion',    'Hyperion moon Saturn sponge irregular Cassini NASA'),
    21: ('Ariel',       'Ariel moon Uranus bright surface Voyager 2 NASA'),
    22: ('Umbriel',     'Umbriel moon Uranus darkest cratered Voyager 2 NASA'),
    23: ('Nix',         'Nix moon Pluto New Horizons NASA elongated'),
    24: ('Hydra',       'Hydra moon Pluto New Horizons NASA photo'),
}

LISTS['xxe'] = {
    1:  ('Première Guerre mondiale','World War I Western Front soldiers trenches barbed wire'),
    2:  ('Révolution russe',        'Russian Revolution 1917 October Bolshevik Petrograd'),
    3:  ('Grande Dépression',       'Great Depression 1929 breadline unemployment Dorothea Lange'),
    4:  ('Deuxième Guerre mondiale','World War II D-Day Normandy Omaha Beach soldiers'),
    5:  ('Nucléaire Hiroshima',     'atomic bomb Hiroshima 1945 mushroom cloud devastation'),
    6:  ('Guerre froide',           'Cold War Berlin Wall soldiers checkpoint checkpoint Charlie'),
    7:  ('Décolonisation',          'decolonization Africa 1960 independence flag ceremony'),
    8:  ('Droits civiques',         'Civil Rights Martin Luther King March Washington DC 1963'),
    9:  ('Course à l\'espace',      'Space Race Apollo Moon landing 1969 astronaut Earth'),
    10: ('Chute du mur Berlin',     'Fall Berlin Wall 1989 hammer crowd celebration Germany'),
    11: ('Internet',                'World Wide Web internet CERN Tim Berners-Lee 1991'),
    12: ('11 Septembre',            'September 11 attacks 2001 Twin Towers New York smoke'),
    13: ('Dissolution URSS',        'Dissolution Soviet Union 1991 Gorbachev Yeltsin flag lowering'),
    14: ('Génocide Rwanda',         'Rwanda genocide 1994 Africa tragedy memorial'),
    15: ('Mondialisation',          'globalization containers ship trade aerial port Rotterdam'),
}

LISTS['montagnes_monde'] = {
    1:  ('Everest',         'Mount Everest summit Himalaya Nepal aerial high resolution'),
    2:  ('K2',              'K2 Karakoram Pakistan aerial second highest peak'),
    3:  ('Kangchenjunga',   'Kangchenjunga Himalaya third highest peak Nepal'),
    4:  ('Lhotse',          'Lhotse Himalaya Nepal fourth highest peak aerial'),
    5:  ('Makalu',          'Makalu Himalaya Nepal aerial fifth highest'),
    6:  ('Cho Oyu',         'Cho Oyu Himalaya Tibet sixth highest peak'),
    7:  ('Dhaulagiri',      'Dhaulagiri Himalaya Nepal aerial'),
    8:  ('Manaslu',         'Manaslu Himalaya Nepal eighth highest aerial'),
    9:  ('Nanga Parbat',    'Nanga Parbat Pakistan Killer Mountain aerial'),
    10: ('Annapurna',       'Annapurna massif Nepal Himalaya aerial South Face'),
    11: ('Aconcagua',       'Aconcagua Andes Argentina highest Americas aerial'),
    12: ('Denali',          'Denali Mount McKinley Alaska aerial snow peak'),
    13: ('Kilimandjaro',    'Kilimanjaro Tanzania snow summit aerial highest Africa'),
    14: ('Elbrouz',         'Elbrus Caucasus Russia snow peak highest Europe aerial'),
    15: ('Mont Blanc',      'Mont Blanc Alps France Italy aerial snow highest Western Europe'),
    16: ('Cervin',          'Matterhorn Zermatt Switzerland iconic peak aerial photo'),
    17: ('Fuji',            'Mount Fuji Japan snow peak reflection lake Kawaguchi'),
    18: ('Popocatépetl',    'Popocatépetl volcano Mexico City eruption smoke aerial'),
    19: ('Vinson',          'Vinson Massif Antarctica aerial snow highest continent'),
    20: ('Puncak Jaya',     'Carstensz Pyramid Puncak Jaya Papua Indonesia glacier'),
    21: ('Ojos del Salado', 'Ojos del Salado volcano Chile Argentina Andes crater aerial'),
    22: ('Mont Logan',      'Mount Logan Yukon Canada highest peak aerial'),
    23: ('Grand Teton',     'Grand Teton Wyoming reflection lake aerial'),
    24: ('Aneto',           'Aneto Pyrenees Spain highest Maladeta glacier aerial'),
    25: ('Olympe',          'Mount Olympus Greece highest peak Mytikas cloud aerial'),
    26: ('St-Hélène',       'Mount St Helens 1980 eruption explosion ash cloud aerial'),
    27: ('Ben Nevis',       'Ben Nevis Scotland highest peak aerial'),
    28: ('Vésuve',          'Mount Vesuvius Naples Italy aerial volcano Pompeii'),
    29: ('Teide',           'Teide Tenerife Canary Islands snow summit aerial'),
    30: ('Montagne de la Table','Table Mountain Cape Town South Africa aerial flat'),
}

LISTS['mers_oceans'] = {
    1:  ('Pacifique',       'Pacific Ocean largest satellite view earth space NASA'),
    2:  ('Atlantique',      'Atlantic Ocean satellite view waves aerial ship'),
    3:  ('Indien',          'Indian Ocean aerial satellite tropical blue'),
    4:  ('Arctique',        'Arctic Ocean sea ice aerial polar bear satellite NASA'),
    5:  ('Antarctique',     'Southern Antarctic Ocean sea ice iceberg aerial'),
    6:  ('Méditerranée',    'Mediterranean Sea aerial satellite coastal turquoise blue'),
    7:  ('Caraïbes',        'Caribbean Sea aerial coral reef turquoise tropical'),
    8:  ('Mer Rouge',       'Red Sea aerial satellite coral reef coral Egypt'),
    9:  ('Baltique',        'Baltic Sea aerial satellite coastline frozen winter'),
    10: ('Mer de Chine',    'South China Sea aerial satellite shoals islands'),
    11: ('Mer de Corail',   'Coral Sea Great Barrier Reef aerial Australia'),
    12: ('Mer de Tasman',   'Tasman Sea New Zealand Australia aerial ocean'),
    13: ("Mer d'Arabie",    'Arabian Sea aerial satellite Oman India shipping'),
    14: ('Golfe du Mexique','Gulf of Mexico aerial satellite oil deepwater Louisiana'),
    15: ('Golfe Persique',  'Persian Gulf aerial satellite oil tanker Arabian'),
    16: ('Mer du Nord',     'North Sea aerial offshore wind farm platform'),
    17: ('Mer Noire',       'Black Sea aerial satellite coastline Turkey Romania'),
    18: ('Mer Caspienne',   'Caspian Sea aerial satellite largest lake landlocked'),
    19: ('Mer Égée',        'Aegean Sea Greece Turkey aerial islands blue turquoise'),
    20: ('Mer Baltique 2',  'Baltic Sea Stockholm archipelago aerial Sweden islands'),
}

LISTS['philosophes'] = {
    1:  ('Socrate',         'Socrates ancient Greek philosopher bust marble Vatican'),
    2:  ('Platon',          'Plato ancient philosopher marble bust Vatican Rome'),
    3:  ('Aristote',        'Aristotle ancient philosopher marble bust Roman copy'),
    4:  ('Épicure',         'Epicurus ancient philosopher Hellenistic marble bust'),
    5:  ('Zénon de Kition', 'Zeno Citium Stoic philosopher ancient marble bust'),
    6:  ('Marc Aurèle',     'Marcus Aurelius Roman emperor philosopher bronze statue equestrian'),
    7:  ('Épictète',        'Epictetus Stoic philosopher ancient portrait painting'),
    8:  ('Saint Augustin',  'Saint Augustine Hippo portrait painting medieval bishop'),
    9:  ('Thomas d\'Aquin', 'Thomas Aquinas Dominican medieval philosopher portrait painting'),
    10: ('Machiavel',       'Niccolò Machiavelli portrait Renaissance painting Santi di Tito'),
    11: ('Francis Bacon',   'Francis Bacon Lord Chancellor portrait English philosopher painting'),
    12: ('Hobbes',          'Thomas Hobbes Leviathan frontispiece portrait painting philosopher'),
    13: ('Descartes',       'René Descartes portrait Frans Hals painting philosopher'),
    14: ('Pascal',          'Blaise Pascal French mathematician portrait painting philosopher'),
    15: ('Locke',           'John Locke portrait painting English philosopher empiricism'),
    16: ('Spinoza',         'Baruch Spinoza portrait philosopher lens grinder'),
    17: ('Leibniz',         'Gottfried Leibniz portrait painting philosopher mathematician'),
    18: ('Montesquieu',     'Montesquieu French philosopher Enlightenment portrait'),
    19: ('Voltaire',        'Voltaire French philosopher portrait Enlightenment irony'),
    20: ('Hume',            'David Hume Scottish philosopher portrait empiricism'),
    21: ('Rousseau',        'Jean-Jacques Rousseau portrait philosopher French'),
    22: ('Adam Smith',      'Adam Smith philosopher economist Wealth Nations portrait'),
    23: ('Kant',            'Immanuel Kant portrait painting philosopher Critique'),
    24: ('Hegel',           'Georg Wilhelm Friedrich Hegel portrait philosopher German'),
    25: ('Schopenhauer',    'Arthur Schopenhauer portrait photographer pessimism will'),
    26: ('Auguste Comte',   'Auguste Comte portrait positivism sociology French'),
    27: ('John Stuart Mill','John Stuart Mill portrait utilitarian philosopher English'),
    28: ('Karl Marx',       'Karl Marx portrait beard Das Kapital Communist Manifesto'),
    29: ('Nietzsche',       'Friedrich Nietzsche portrait photograph mustache philosopher'),
    30: ('Husserl',         'Edmund Husserl portrait phenomenology German philosopher'),
    31: ('Bergson',         'Henri Bergson French philosopher Nobel portrait photograph'),
    32: ('Bertrand Russell','Bertrand Russell portrait British philosopher logical atomism'),
    33: ('Wittgenstein',    'Ludwig Wittgenstein portrait Austrian philosopher language'),
    34: ('Heidegger',       'Martin Heidegger portrait philosopher Being Time German'),
    35: ('Hannah Arendt',   'Hannah Arendt portrait philosopher woman German American'),
    36: ('Sartre',          'Jean-Paul Sartre portrait philosopher pipe existentialism'),
    37: ('Simone de Beauvoir','Simone de Beauvoir portrait philosopher feminist Second Sex'),
    38: ('Camus',           'Albert Camus portrait French philosopher Nobel absurd'),
    39: ('Lévi-Strauss',    'Claude Lévi-Strauss portrait anthropologist structuralism'),
    40: ('Foucault',        'Michel Foucault portrait philosopher French bald'),
    41: ('Deleuze',         'Gilles Deleuze portrait philosopher French Difference'),
    42: ('Derrida',         'Jacques Derrida portrait philosopher French deconstruction'),
    43: ('Rawls',           'John Rawls portrait philosopher American Theory of Justice'),
    44: ('Habermas',        'Jürgen Habermas portrait philosopher German Frankfurt'),
    45: ('Peter Singer',    'Peter Singer portrait philosopher Australian ethics animal'),
}

LISTS['xixe'] = {
    1:  ('Napoléon 1800',           'Napoleon Bonaparte First Consul 1800 portrait David painting'),
    2:  ('Couronnement 1804',       'Napoleon coronation 1804 Notre-Dame David painting detail'),
    3:  ('Austerlitz 1805',         'Battle Austerlitz 1805 Napoleon painting three emperors'),
    4:  ('Abolition Saint-Empire 1806','Holy Roman Empire dissolution 1806 Francis II map'),
    5:  ('Traité de Tilsit 1807',   'Treaty Tilsit 1807 Napoleon Alexander I raft Niemen'),
    6:  ('Espagne 1808',            'Goya Third of May 1808 Spanish painting execution Prado'),
    7:  ('Russie 1812',             'French invasion Russia 1812 retreat Napoleon Moscow burning'),
    8:  ('Leipzig 1813',            'Battle Leipzig 1813 nations Napoleon defeat painting'),
    9:  ('Congrès de Vienne 1815',  'Congress Vienna 1815 diplomats meeting Metternich map'),
    10: ('Waterloo 1815',           'Battle Waterloo 1815 Napoleon defeat Wellington cavalry painting'),
    11: ('Tambora 1816',            'Tambora volcano eruption 1816 year without summer'),
    12: ('Peterloo 1819',           'Peterloo massacre 1819 Manchester cavalry crowd charge'),
    13: ('Grèce indépendance 1821', 'Greek independence war 1821 Delacroix Greece ruins painting'),
    14: ('9e symphonie 1824',       'Beethoven Symphony 9 Choral 1824 musical score manuscript'),
    15: ('Chemin de fer 1825',      'Stephenson Locomotion railway 1825 Stockton Darlington steam'),
    16: ('Révolution juillet 1830', 'July Revolution 1830 Paris barricades Delacroix Liberty painting'),
    17: ('Faraday induction 1831',  'Faraday electromagnetic induction 1831 coil magnet laboratory'),
    18: ('Loi réforme 1832',        'Reform Act 1832 Parliament British electoral map vote'),
    19: ('Abolition esclavage 1833','Abolition Slavery 1833 Britain Wilberforce West Indies freedom'),
    20: ('Reine Victoria 1837',     'Queen Victoria coronation 1837 portrait young monarch throne'),
    21: ('Guerre opium 1839',       'First Opium War 1839 British Chinese Canton Pearl River ships'),
    22: ('Traité Waitangi 1840',    'Treaty Waitangi 1840 New Zealand Maori British signing'),
    23: ('Grande Famine 1845',      'Great Famine Ireland 1845 potato blight emigration coffin ship'),
    24: ('Découverte Neptune 1846', 'Neptune planet discovery 1846 Galle Le Verrier telescope'),
    25: ('Révolutions 1848',        'Revolutions 1848 barricades Paris spring peoples painting'),
    26: ('Or Californie 1849',      'California Gold Rush 1849 forty-niners prospectors panning'),
    27: ('Exposition 1851',         'Great Exhibition 1851 Crystal Palace London Hyde Park interior'),
    28: ('Second Empire 1852',      'Napoleon III Second Empire 1852 proclamation imperial portrait'),
    29: ('Guerre Crimée 1853',      'Crimean War 1854 soldiers charge Balaclava photograph'),
    30: ('Darwin 1859',             'Darwin On the Origin of Species 1859 book cover title page'),
    31: ('Unification Italie 1861', 'Italian unification Risorgimento 1861 Garibaldi Cavour portrait'),
    32: ('Guerre Sécession 1861',   'American Civil War 1861 Gettysburg Battle soldiers cannon'),
    33: ('Proclamation Émancipation','Lincoln Emancipation Proclamation 1863 slaves freedom USA'),
    34: ('Croix-Rouge 1864',        'Red Cross Geneva Convention 1864 Dunant Solferino wounded'),
    35: ('Assassinat Lincoln 1865', 'Lincoln assassination 1865 Ford Theatre booth photograph'),
    36: ('Bismarck Prusse 1866',    'Austro-Prussian War 1866 Königgrätz Bismarck German unification'),
    37: ('Alaska 1867',             'Alaska Purchase 1867 Seward Russia USA transfer check map'),
    38: ('Meiji 1868',              'Meiji Restoration 1868 Japan Emperor modernization samurai'),
    39: ('Canal Suez 1869',         'Suez Canal opening 1869 Egypt ships fireworks Ismailia'),
    40: ('Franco-prussien 1870',    'Franco-Prussian War 1870 Sedan Napoleon III German siege'),
    41: ('Commune Paris 1871',      'Paris Commune 1871 Communards barricades Semaine Sanglante'),
    42: ('Téléphone 1876',          'Alexander Graham Bell telephone invention 1876 laboratory'),
    43: ('Little Bighorn 1876',     'Battle Little Bighorn 1876 Custer defeat Sioux Lakota Sitting Bull'),
    44: ('Lumière Edison 1879',     'Edison light bulb filament incandescent 1879 laboratory Menlo Park'),
    45: ('Tsar Alexandre II 1881',  'Alexander II assassination 1881 bomb carriage St Petersburg Russia'),
    46: ('Alliance triple 1882',    'Triple Alliance 1882 Germany Austria-Hungary Italy Bismarck map'),
    47: ('Benz automobile 1885',    'Benz Patent-Motorwagen 1885 first automobile three wheel'),
    48: ('Statue Liberté 1886',     'Statue of Liberty dedication 1886 New York Harbor Bedloe'),
    49: ('Tour Eiffel 1889',        'Eiffel Tower 1889 construction Paris Exposition Universelle aerial'),
    50: ('Wounded Knee 1890',       'Wounded Knee massacre 1890 Native American Sioux Ghost Dance'),
    51: ('Affaire Dreyfus 1894',    'Dreyfus Affair 1894 France anti-semitism J\'Accuse Zola trial'),
    52: ('Cinéma Lumière 1895',     'Lumière brothers cinematograph 1895 Grand Café screening Paris'),
    53: ('Jeux olympiques 1896',    'Athens 1896 first modern Olympic Games Panathenaic stadium'),
    54: ('Sionisme 1897',           'First Zionist Congress 1897 Herzl Basel Jewish state declaration'),
    55: ('Hispano-américaine 1898', 'Spanish-American War 1898 Cuba USS Maine San Juan Hill soldiers'),
    56: ('Guerre des Boers 1899',   'Second Boer War 1899 South Africa British soldiers Ladysmith'),
    57: ('Marie Curie Nobel 1903',  'Marie Curie Nobel Prize 1903 laboratory portrait radium'),
    58: ('Avion 1903',              'Wright brothers Flyer 1903 Kitty Hawk first flight Orville'),
    59: ('Révolution Russe 1905',   'Russian Revolution 1905 Bloody Sunday St Petersburg workers'),
    60: ('Tremblement SF 1906',     'San Francisco earthquake 1906 fire destruction photograph'),
    61: ('Ford T 1908',             'Ford Model T automobile 1908 assembly line mass production'),
    62: ('Titanic 1912',            'Titanic ship 1912 sinking iceberg White Star liner'),
    63: ('Première Guerre 1914',    'World War I 1914 assassination Sarajevo Franz Ferdinand'),
    64: ('Révolution Mexicaine 1910','Mexican Revolution 1910 Zapata Villa peasants portrait'),
    65: ('Théorie relativité 1905', 'Einstein special relativity theory 1905 E=mc2 Albert'),
    66: ('Radio Marconi 1895',      'Marconi wireless telegraphy 1895 radio transmission antenna'),
    67: ('Peinture Cézanne',        'Cézanne Post-Impressionism painting landscape portrait apples'),
    68: ('Exposition universelle 1900','Paris Universal Exhibition 1900 Grand Palais Eiffel Tower'),
    69: ('Canal Panama 1889',       'Panama Canal construction 1904 lock workers aerial French'),
    70: ('Seconde Révolution Ind.',  'Second Industrial Revolution steel factory workers 1880s'),
    71: ('Colonialisme Afrique',    'Berlin Conference 1884 Africa partition colonial scramble map'),
    72: ('Suez canal 1869',         'Suez Canal 1869 inauguration De Lesseps Egypt desert ships'),
    73: ('Philosophie Nietzsche',   'Nietzsche philosopher portrait mustache Beyond Good Evil'),
    74: ('Rimbaud Verlaine',        'Arthur Rimbaud portrait French Symbolist poet young photograph'),
    75: ('Expositions Beaux-Arts',  'Belle Époque Paris 1900 Impressionism Salon exhibition art'),
}

# ── Exécution ──────────────────────────────────────────────────────────────────
total_ok = total_fail = 0
for folder, entries in LISTS.items():
    if folder in SKIP:
        continue
    ok, fail = process(folder, entries)
    total_ok += ok
    total_fail += fail

LOG.close()
FAIL.close()
print(f'\n╔═════════════════════════╗')
print(f'║ TOTAL OK   : {total_ok:5d}     ║')
print(f'║ TOTAL FAIL : {total_fail:5d}     ║')
print(f'╚═════════════════════════╝')
