"""
Upgrade TOUTES les full/ images en vraie haute qualité.
Stratégie : piprop=original (image d'origine Wikipedia) → redimensionne à 1200px max.
Contrairement à pithumbsize=1200, cela donne réellement 1200px (Wikipedia ne capote pas à 800).
"""
import sys, pathlib, requests, time
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
from PIL import Image
from io import BytesIO
from lib_img import get_original_url, get_thumb_url

BASE = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')
FULL = BASE / 'full'
HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact: claude.elk041@passmail.net)'}

# Listes à NE PAS toucher
SKIP_FOLDERS = {'pays', 'departements', 'etats_usa', 'elements',
                'periodes_geologiques', 'vocabulaire_precis', 'phrasal_verbs', 'os'}

OK_LOG  = open(BASE / 'build' / 'upgrade_hq_ok.txt',  'w', encoding='utf-8')
FAIL_LOG = open(BASE / 'build' / 'upgrade_hq_fails.txt', 'w', encoding='utf-8')

def save_full(url, folder, num):
    """Télécharge url, redimensionne à 1200px max, sauvegarde en JPEG q88."""
    r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
    content = r.content
    if len(content) < 1000:
        raise ValueError(f'Trop petit ({len(content)} octets)')
    img = Image.open(BytesIO(content)).convert('RGB')
    w0, h0 = img.size
    img.thumbnail((1200, 1200), Image.LANCZOS)
    # Supprimer l'ancien fichier quelle que soit l'extension
    for old in (FULL / folder).glob(f'{num}.*'):
        old.unlink()
    out = FULL / folder / f'{num}.jpg'
    img.save(out, 'JPEG', quality=88, optimize=True)
    kb = out.stat().st_size // 1024
    print(f'  #{num}: {w0}x{h0} → {img.size[0]}x{img.size[1]} {kb}KB')
    return img.size[0]


# ─── Données complètes par liste ──────────────────────────────────────────────
LIST_DATA = {

'peintres': {
    1:'Jan van Eyck', 2:'Sandro Botticelli', 3:'Leonardo da Vinci', 4:'Albrecht Dürer',
    5:'Michelangelo', 6:'Raphael (painter)', 7:'Titian', 8:'Pieter Bruegel the Elder',
    9:'Caravaggio', 10:'Rembrandt', 11:'Nicolas Poussin', 12:'Rembrandt',
    13:'Johannes Vermeer', 14:'Francisco Goya', 15:'Jacques-Louis David',
    16:'Caspar David Friedrich', 17:'Eugène Delacroix', 18:'Gustave Courbet',
    19:'Édouard Manet', 20:'Claude Monet', 21:'Pierre-Auguste Renoir',
    22:'Edgar Degas', 23:'Paul Cézanne', 24:'Georges Seurat', 25:'Vincent van Gogh',
    26:'Paul Gauguin', 27:'Henri de Toulouse-Lautrec', 28:'Gustav Klimt',
    29:'Edvard Munch', 30:'Henri Matisse', 31:'Pablo Picasso', 32:'Wassily Kandinsky',
    33:'Edward Hopper', 34:'Amedeo Modigliani', 35:'Diego Rivera',
    36:'Marcel Duchamp', 37:'Giorgio de Chirico', 38:'René Magritte',
    39:'Salvador Dalí', 40:'Frida Kahlo', 41:'Jackson Pollock', 42:'Mark Rothko',
    43:'Andy Warhol', 44:'Roy Lichtenstein', 45:'Francis Bacon (artist)',
    46:'Lucian Freud', 47:'David Hockney', 48:'Gerhard Richter', 49:'Jean-Michel Basquiat',
    50:'Banksy',
},

'musees_monde': {
    1:'Louvre Museum', 2:'Metropolitan Museum of Art', 3:'British Museum',
    4:'Hermitage Museum', 5:'Vatican Museums', 6:'Uffizi Gallery',
    7:'Prado Museum', 8:'Rijksmuseum', 9:'Musée d\'Orsay', 10:'Tate Modern',
    11:'Museum of Modern Art', 12:'Guggenheim Museum', 13:'National Gallery (London)',
    14:'Smithsonian Institution', 15:'Acropolis Museum', 16:'Egyptian Museum, Cairo',
    17:'Tokyo National Museum', 18:'National Museum of China',
    19:'Pergamon Museum', 20:'Dresden Gallery', 21:'Pinacoteca di Brera',
    22:'Topkapı Palace', 23:'Château de Versailles', 24:'Centre Pompidou',
    25:'Stedelijk Museum Amsterdam',
},

'parcs_nationaux': {
    1:'Yellowstone National Park', 2:'Grand Canyon National Park', 3:'Yosemite National Park',
    4:'Great Barrier Reef Marine Park', 5:'Serengeti National Park', 6:'Amazon rainforest',
    7:'Torres del Paine National Park', 8:'Galápagos National Park',
    9:'Fiordland National Park', 10:'Banff National Park', 11:'Kruger National Park',
    12:'Everglades National Park', 13:'Machu Picchu', 14:'Zhangjiajie National Forest Park',
    15:'Komodo National Park', 16:'Kilimanjaro National Park', 17:'Iguazu National Park',
    18:'Denali National Park', 19:'Glacier National Park', 20:'Arches National Park',
    21:'Tongariro National Park', 22:'Dolomites', 23:'Cévennes National Park',
    24:'Lake District National Park', 25:'Ha Long Bay',
},

'compositeurs': {
    1:'Johann Sebastian Bach', 2:'George Frideric Handel', 3:'Antonio Vivaldi',
    4:'Wolfgang Amadeus Mozart', 5:'Ludwig van Beethoven', 6:'Franz Schubert',
    7:'Frédéric Chopin', 8:'Robert Schumann', 9:'Franz Liszt', 10:'Richard Wagner',
    11:'Giuseppe Verdi', 12:'Johannes Brahms', 13:'Antonín Dvořák',
    14:'Pyotr Ilyich Tchaikovsky', 15:'Giacomo Puccini', 16:'Gustav Mahler',
    17:'Claude Debussy', 18:'Maurice Ravel', 19:'Igor Stravinsky', 20:'Béla Bartók',
    21:'Sergei Prokofiev', 22:'Dmitri Shostakovich', 23:'Arnold Schoenberg',
    24:'Alban Berg', 25:'Anton Webern',
},

'mouvements_peinture': {
    1:'Byzantine art', 2:'Romanesque art', 3:'Gothic art', 4:'Early Netherlandish painting',
    5:'Italian Renaissance', 6:'Mannerism', 7:'Baroque painting', 8:'Dutch Golden Age painting',
    9:'Rococo', 10:'Neoclassicism', 11:'Romanticism', 12:'Realism (arts)',
    13:'Barbizon school', 14:'Pre-Raphaelite Brotherhood', 15:'Impressionism',
    16:'Post-Impressionism', 17:'Symbolism (arts)', 18:'Art Nouveau',
    19:'Fauvism', 20:'Expressionism', 21:'Cubism', 22:'Futurism (art)',
    23:'Constructivism (art)', 24:'De Stijl', 25:'Dadaism',
    26:'Surrealism', 27:'Abstract expressionism', 28:'Pop art', 29:'Minimalism',
    30:'Conceptual art', 31:'Hyperrealism (painting)', 32:'Street art',
    33:'Surrealism', 34:'Abstract expressionism', 35:'Neo-Expressionism',
    36:'Photorealism', 37:'Arte Povera', 38:'Fluxus', 39:'Neo-Expressionism',
},

'architectes': {
    1:'Andrea Palladio', 2:'Christopher Wren', 3:'Gian Lorenzo Bernini',
    4:'Gustave Eiffel', 5:'Antoni Gaudí', 6:'Otto Wagner', 7:'Le Corbusier',
    8:'Frank Lloyd Wright', 9:'Ludwig Mies van der Rohe', 10:'Walter Gropius',
    11:'Alvar Aalto', 12:'Oscar Niemeyer', 13:'Louis Kahn', 14:'Jørn Utzon',
    15:'Renzo Piano', 16:'Richard Rogers (architect)', 17:'Norman Foster',
    18:'Frank Gehry', 19:'Tadao Ando', 20:'Zaha Hadid',
    21:'Rem Koolhaas', 22:'Jean Nouvel', 23:'Santiago Calatrava', 24:'Peter Zumthor',
    25:'Bjarke Ingels',
},

'decouvertes_scientifiques': {
    1:'Heliocentrism', 2:'Gravity', 3:'Calculus', 4:'Laws of thermodynamics',
    5:'Electromagnetism', 6:'Theory of evolution', 7:'Germ theory of disease',
    8:'Periodic table', 9:'X-ray', 10:'Radioactivity', 11:'Theory of relativity',
    12:'Quantum mechanics', 13:'DNA', 14:'Penicillin', 15:'Big Bang',
    16:'Plate tectonics', 17:'Higgs boson', 18:'Gravitational wave', 19:'CRISPR',
    20:'Exoplanet',
},

'grands_scientifiques': {
    1:'Isaac Newton', 2:'Galileo Galilei', 3:'Albert Einstein', 4:'Charles Darwin',
    5:'Marie Curie', 6:'Louis Pasteur', 7:'Nikola Tesla', 8:'Michael Faraday',
    9:'James Clerk Maxwell', 10:'Max Planck', 11:'Niels Bohr', 12:'Werner Heisenberg',
    13:'Richard Feynman', 14:'Erwin Schrödinger', 15:'Gregor Mendel',
    16:'Johannes Kepler', 17:'René Descartes', 18:'Blaise Pascal',
    19:'Leonhard Euler', 20:'Carl Friedrich Gauss', 21:'James Watt',
    22:'Antoine Lavoisier', 23:'Humphry Davy', 24:'Alessandro Volta',
    25:'André-Marie Ampère', 26:'James Joule', 27:'Lord Kelvin',
    28:'Heinrich Hertz', 29:'Wilhelm Röntgen', 30:'Ernest Rutherford',
    31:'Enrico Fermi', 32:'Robert Oppenheimer', 33:'Linus Pauling',
    34:'Francis Crick', 35:'James Watson', 36:'Stephen Hawking',
},

'grandes_explorations': {
    1:'Christopher Columbus', 2:'Vasco da Gama', 3:'Ferdinand Magellan',
    4:'Amerigo Vespucci', 5:'John Cabot', 6:'Francis Drake',
    7:'Henry Hudson', 8:'Abel Tasman', 9:'James Cook', 10:'Alexander von Humboldt',
    11:'Meriwether Lewis', 12:'William Clark', 13:'René-Robert Cavelier de La Salle',
    14:'Jacques Cartier', 15:'Henry the Navigator', 16:'Samuel de Champlain',
    17:'David Livingstone', 18:'Mungo Park (explorer)', 19:'Roald Amundsen',
    20:'Ernest Shackleton', 21:'Robert Falcon Scott', 22:'Edmund Hillary',
    23:'Yuri Gagarin', 24:'Neil Armstrong', 25:'Valentina Tereshkova',
},

'inventions_majeures': {
    1:'Wheel', 2:'Writing system', 3:'Printing press', 4:'Steam engine',
    5:'Telephone', 6:'Lightbulb', 7:'Automobile', 8:'Airplane',
    9:'Television', 10:'Penicillin', 11:'Computer', 12:'Internet',
    13:'Transistor', 14:'Laser', 15:'Plastic', 16:'Nuclear reactor',
    17:'Satellite', 18:'Integrated circuit', 19:'World Wide Web',
    20:'Smartphone', 21:'GPS', 22:'3D printing',
    23:'Gunpowder', 24:'Compass', 25:'Clock', 26:'Telescope',
    27:'Microscope', 28:'Vaccination', 29:'Railway', 30:'Radio',
},

'civilisations': {
    1:'Ancient Egypt', 2:'Mesopotamia', 3:'Ancient Greece', 4:'Roman Empire',
    5:'Persian Empire', 6:'Chinese civilization', 7:'Indus Valley Civilisation',
    8:'Maya civilization', 9:'Aztec Empire', 10:'Inca Empire',
    11:'Byzantine Empire', 12:'Islamic Golden Age', 13:'Viking Age',
    14:'Holy Roman Empire', 15:'Mongol Empire', 16:'Ottoman Empire',
    17:'Mughal Empire', 18:'British Empire', 19:'Carolingian Empire',
    20:'Ancient Carthage', 21:'Minoan civilization', 22:'Phoenicia',
    23:'Hittites', 24:'Ancient Nubia', 25:'Mughal Empire',
},

'litterature': {
    1:'Iliad', 2:'Odyssey', 3:'Aeneid', 4:'Metamorphoses (Ovid)',
    5:'Divine Comedy', 6:'The Decameron', 7:'Don Quixote',
    8:'William Shakespeare', 9:'Hamlet', 10:'King Lear',
    11:'Essays (Montaigne)', 12:'Candide', 13:'Gulliver\'s Travels',
    14:'Les Misérables', 15:'The Red and the Black', 16:'The Charterhouse of Parma',
    17:'Père Goriot', 18:'Madame Bovary', 19:'Crime and Punishment',
    20:'The Brothers Karamazov', 21:'War and Peace', 22:'Anna Karenina',
    23:'The Idiot (novel)', 24:'Adventures of Huckleberry Finn', 25:'Moby-Dick',
    26:'Wuthering Heights', 27:'Jane Eyre', 28:'The Picture of Dorian Gray',
    29:'In Search of Lost Time', 30:'Ulysses (novel)', 31:'Mrs Dalloway',
    32:'The Great Gatsby', 33:'The Stranger (Camus novel)', 34:'Nausea (Sartre)',
    35:'The Trial (novel)', 36:'The Castle (novel)', 37:'Faust, Part One',
    38:'Animal Farm', 39:'Nineteen Eighty-Four', 40:'Brave New World',
    41:'The Lord of the Rings', 42:'The Catcher in the Rye',
    43:'On the Road', 44:'One Hundred Years of Solitude',
    45:'The Master and Margarita', 46:'Lolita (novel)',
    47:'The Sound and the Fury', 48:'Beloved (novel)',
    49:'The Name of the Rose', 50:'The Grapes of Wrath',
    51:'Les Fleurs du mal', 52:'Journey to the End of the Night',
    53:"Man's Fate", 54:'Dune (novel)', 55:'Foundation (Asimov novel)',
    56:"The Hitchhiker's Guide to the Galaxy", 57:'Harry Potter and the Philosopher\'s Stone',
    58:'The Alchemist (novel)',
},

'guerres': {
    1:'Trojan War', 2:'Greco-Persian Wars', 3:'Peloponnesian War',
    4:'Punic Wars', 5:'Gallic Wars', 6:'Hundred Years\' War',
    7:'Crusades', 8:'Mongol invasions', 9:'Ottoman wars in Europe',
    10:'Thirty Years\' War', 11:'American Revolutionary War',
    12:'Napoleonic Wars', 13:'Crimean War', 14:'American Civil War',
    15:'Franco-Prussian War', 16:'World War I', 17:'World War II',
    18:'Korean War', 19:'Vietnam War', 20:'Gulf War', 21:'War in Afghanistan',
    22:'Iraq War',
},

'rois_france': {
    1:'Clovis I', 2:'Chlothar I', 3:'Chilperic I', 4:'Chlothar II', 5:'Dagobert I',
    6:'Clovis II', 7:'Chlothar III', 8:'Theuderic III', 9:'Clovis IV', 10:'Childebert III',
    11:'Dagobert III', 12:'Chilperic II', 13:'Theuderic IV', 14:'Childeric III',
    15:'Pepin the Short', 16:'Charlemagne', 17:'Louis the Pious', 18:'Charles the Bald',
    19:'Louis the Stammerer', 20:'Louis III of France', 21:'Carloman II of France',
    22:'Charles the Fat', 23:'Odo, Count of Paris', 24:'Charles the Simple',
    25:'Robert I of France', 26:'Rudolph of France', 27:'Louis IV of France',
    28:'Lothair of France', 29:'Louis V of France', 30:'Hugh Capet',
    31:'Robert II of France', 32:'Henry I of France', 33:'Philip I of France',
    34:'Louis VI of France', 35:'Louis VII of France', 36:'Philip II of France',
    37:'Louis VIII of France', 38:'Louis IX of France', 39:'Philip III of France',
    40:'Philip IV of France', 41:'Louis X of France', 42:'John I of France',
    43:'Philip V of France', 44:'Charles IV of France', 45:'Philip VI of France',
    46:'John II of France', 47:'Charles V of France', 48:'Charles VI of France',
    49:'Charles VII of France', 50:'Louis XI of France', 51:'Charles VIII of France',
    52:'Louis XII of France', 53:'Francis I of France', 54:'Henry II of France',
    55:'Francis II of France', 56:'Charles IX of France', 57:'Henry III of France',
    58:'Henry IV of France', 59:'Louis XIII', 60:'Louis XIV',
    61:'Louis XV', 62:'Louis XVI', 63:'Napoleon', 64:'Louis XVIII',
    65:'Charles X', 66:'Louis Philippe I',
},

'mythologie': {
    1:'Zeus', 2:'Hera', 3:'Poseidon', 4:'Demeter', 5:'Athena',
    6:'Apollo', 7:'Artemis', 8:'Ares', 9:'Aphrodite', 10:'Hephaestus',
    11:'Hermes', 12:'Dionysus', 13:'Hades', 14:'Persephone', 15:'Hestia',
    16:'Nyx', 17:'Chaos (cosmogony)', 18:'Cronus', 19:'Hecate', 20:'Thanatos',
    21:'Hypnos', 22:'Charon (mythology)', 23:'Eros', 24:'Nike (mythology)',
    25:'Prometheus', 26:'Atlas (mythology)', 27:'Helios', 28:'Selene (goddess)',
    29:'Pan (god)', 30:'Dionysus', 31:'Asclepius', 32:'Heracles',
    33:'Achilles', 34:'Odysseus', 35:'Theseus', 36:'Minotaur',
    37:'Orpheus', 38:'Eurydice (mythology)', 39:'Sisyphus', 40:'Perseus',
    41:'Medusa', 42:'Icarus', 43:'Daedalus', 44:'Narcissus (mythology)',
    45:'Echo (mythology)', 46:'Arachne', 47:'Oedipus', 48:'Pandora',
    49:'Eris (mythology)', 50:'Helios', 51:'Selene (goddess)', 52:'Tyche',
    53:'Aeolus', 54:'Cerberus', 55:'Medea', 56:'Jason (mythology)',
    57:'Tantalus', 58:'Ixion', 59:'Hyperion (Titan)',
},

'batailles_decisives': {
    1:'Battle of Marathon', 2:'Battle of Hastings', 3:'Battle of Bouvines', 4:'Battle of Waterloo',
    5:'Battle of Verdun', 6:'Battle of Stalingrad', 7:'Battle of Midway',
    8:'Battle of Dien Bien Phu', 9:'Battle of Gaugamela', 10:'Battle of Cannae',
    11:'Battle of Actium', 12:'Battle of the Catalaunian Plains', 13:'Battle of Yarmouk',
    14:'Battle of Tours', 15:'Battle of Lepanto', 16:'Battle of Rocroi', 17:'Battle of Poltava',
    18:'Battle of Plassey', 19:'Siege of Yorktown (1781)', 20:'Battle of Valmy',
    21:'Battle of Austerlitz', 22:'Battle of Leipzig', 23:'Battle of Tsushima',
    24:'Battle of the Marne (1914)', 25:'Battle of the Somme', 26:'Second Battle of El Alamein',
    27:'Battle of Kursk', 28:'Normandy landings', 29:'Battle of Berlin (1945)',
    30:'Battle of Inchon', 31:'Yom Kippur War', 32:'Falklands War', 33:'Gulf War',
},

'fleuves_monde': {
    1:'Nile', 2:'Amazon River', 3:'Yangtze River', 4:'Mississippi River',
    5:'Yenisei River', 6:'Yellow River', 7:'Ob River', 8:'Paraná River', 9:'Congo River',
    10:'Amur River', 11:'Lena River', 12:'Mekong', 13:'Niger River', 14:'Mackenzie River',
    15:'Volga', 16:'Zambezi', 17:'Orinoco', 18:'Euphrates', 19:'Tigris',
    20:'Ganges', 21:'Indus River', 22:'Murray River', 23:'Danube', 24:'Saint Lawrence River',
    25:'Colorado River (United States)', 26:'Rio Grande', 27:'Orange River',
    28:'Rhine', 29:'Senegal River', 30:'Irrawaddy River',
},

'constellations': {
    1:'Orion (constellation)', 2:'Ursa Major', 3:'Ursa Minor', 4:'Cassiopeia (constellation)',
    5:'Scorpius', 6:'Leo (constellation)', 7:'Virgo (constellation)', 8:'Gemini (constellation)',
    9:'Aquarius (constellation)', 10:'Pisces (constellation)', 11:'Aries (constellation)',
    12:'Taurus (constellation)', 13:'Cancer (constellation)', 14:'Libra (constellation)',
    15:'Sagittarius (constellation)', 16:'Capricornus', 17:'Perseus (constellation)',
    18:'Andromeda (constellation)', 19:'Cygnus (constellation)', 20:'Lyra (constellation)',
    21:'Aquila (constellation)', 22:'Hercules (constellation)', 23:'Boötes (constellation)',
    24:'Draco (constellation)', 25:'Centaurus (constellation)', 26:'Crux',
    27:'Canis Major', 28:'Canis Minor', 29:'Hydra (constellation)', 30:'Eridanus (constellation)',
    31:'Ophiuchus', 32:'Serpens', 33:'Corona Borealis', 34:'Auriga (constellation)',
    35:'Pegasus (constellation)', 36:'Cetus', 37:'Piscis Austrinus', 38:'Lupus (constellation)',
},

'detroits_monde': {
    1:'Strait of Gibraltar', 2:'Bosphorus', 3:'Dardanelles', 4:'Strait of Hormuz',
    5:'Strait of Malacca', 6:'Bering Strait', 7:'Strait of Magellan',
    8:'Bab-el-Mandeb', 9:'Strait of Dover', 10:'Strait of Messina',
    11:'Skagerrak', 12:'Taiwan Strait', 13:'Korea Strait', 14:'Lombok Strait',
    15:'Bass Strait', 16:'Straits of Florida', 17:'Øresund',
    18:'Mozambique Channel', 19:'Singapore Strait', 20:'Tsugaru Strait',
},

'revolutions': {
    1:'American Revolution', 2:'French Revolution', 3:'Haitian Revolution',
    4:'Latin American wars of independence', 5:'Revolutions of 1848',
    6:'Meiji Restoration', 7:'Russian Revolution', 8:'Chinese Revolution (1911)',
    9:'Mexican Revolution', 10:'Turkish War of Independence', 11:'Indian independence movement',
    12:'Chinese Communist Revolution', 13:'Cuban Revolution', 14:'Iranian Revolution',
    15:'Velvet Revolution', 16:'Fall of the Berlin Wall',
},

'chefs_etat': {
    1:'George Washington', 2:'Abraham Lincoln', 3:'Napoleon', 4:'Winston Churchill',
    5:'Charles de Gaulle', 6:'Otto von Bismarck', 7:'Vladimir Lenin',
    8:'Joseph Stalin', 9:'Adolf Hitler', 10:'Benito Mussolini',
    11:'Franklin D. Roosevelt', 12:'Mao Zedong', 13:'Mahatma Gandhi',
    14:'Nelson Mandela', 15:'John F. Kennedy', 16:'Fidel Castro',
    17:'Che Guevara', 18:'Ho Chi Minh', 19:'Jawaharlal Nehru',
    20:'Simón Bolívar', 21:'Otto von Bismarck', 22:'Kemal Atatürk',
    23:'Franklin D. Roosevelt', 24:'Harry S. Truman', 25:'Dwight D. Eisenhower',
},

'jo_ete': {
    1:'1896 Summer Olympics', 2:'1900 Summer Olympics', 3:'1904 Summer Olympics',
    4:'1906 Intercalated Games', 5:'1908 Summer Olympics', 6:'1912 Summer Olympics',
    7:'1920 Summer Olympics', 8:'1924 Summer Olympics', 9:'1928 Summer Olympics',
    10:'1932 Summer Olympics', 11:'1936 Summer Olympics', 12:'1948 Summer Olympics',
    13:'1952 Summer Olympics', 14:'1956 Summer Olympics', 15:'1960 Summer Olympics',
    16:'1964 Summer Olympics', 17:'1968 Summer Olympics', 18:'1972 Summer Olympics',
    19:'1976 Summer Olympics', 20:'1980 Summer Olympics', 21:'1984 Summer Olympics',
    22:'1988 Summer Olympics', 23:'1992 Summer Olympics', 24:'1996 Summer Olympics',
    25:'2000 Summer Olympics', 26:'2004 Summer Olympics', 27:'2008 Summer Olympics',
    28:'2012 Summer Olympics', 29:'2016 Summer Olympics', 30:'2020 Summer Olympics',
    31:'2024 Summer Olympics',
},

'jo_hiver': {
    1:'1924 Winter Olympics', 2:'1928 Winter Olympics', 3:'1932 Winter Olympics',
    4:'1936 Winter Olympics', 5:'1948 Winter Olympics', 6:'1952 Winter Olympics',
    7:'1956 Winter Olympics', 8:'1960 Winter Olympics', 9:'1964 Winter Olympics',
    10:'1968 Winter Olympics', 11:'1972 Winter Olympics', 12:'1976 Winter Olympics',
    13:'1980 Winter Olympics', 14:'1984 Winter Olympics', 15:'1988 Winter Olympics',
    16:'1992 Winter Olympics', 17:'1994 Winter Olympics', 18:'1998 Winter Olympics',
    19:'2002 Winter Olympics', 20:'2006 Winter Olympics', 21:'2010 Winter Olympics',
    22:'2014 Winter Olympics', 23:'2018 Winter Olympics', 24:'2022 Winter Olympics',
    25:'2026 Winter Olympics',
},

'coupes_monde': {
    1:'1930 FIFA World Cup', 2:'1934 FIFA World Cup', 3:'1938 FIFA World Cup',
    4:'1950 FIFA World Cup', 5:'1954 FIFA World Cup', 6:'1958 FIFA World Cup',
    7:'1962 FIFA World Cup', 8:'1966 FIFA World Cup', 9:'1970 FIFA World Cup',
    10:'1974 FIFA World Cup', 11:'1978 FIFA World Cup', 12:'1982 FIFA World Cup',
    13:'1986 FIFA World Cup', 14:'1990 FIFA World Cup', 15:'1994 FIFA World Cup',
    16:'1998 FIFA World Cup', 17:'2002 FIFA World Cup', 18:'2006 FIFA World Cup',
    19:'2010 FIFA World Cup', 20:'2014 FIFA World Cup', 21:'2018 FIFA World Cup',
    22:'2022 FIFA World Cup',
},

'f1_champions': {
    1:'Giuseppe Farina', 2:'Alberto Ascari', 3:'Juan Manuel Fangio',
    4:'Mike Hawthorn', 5:'Jack Brabham', 6:'Phil Hill', 7:'Graham Hill',
    8:'Jim Clark', 9:'John Surtees', 10:'Denny Hulme',
    11:'Jackie Stewart', 12:'Emerson Fittipaldi', 13:'Niki Lauda',
    14:'James Hunt', 15:'Mario Andretti', 16:'Jody Scheckter',
    17:'Alan Jones', 18:'Nelson Piquet', 19:'Keke Rosberg',
    20:'Alain Prost', 21:'Ayrton Senna', 22:'Nigel Mansell',
    23:'Michael Schumacher', 24:'Damon Hill', 25:'Jacques Villeneuve',
    26:'Mika Häkkinen', 27:'Kimi Räikkönen', 28:'Fernando Alonso',
    29:'Jenson Button', 30:'Sebastian Vettel', 31:'Lewis Hamilton',
    32:'Max Verstappen',
},

'consoles': {
    1:'Magnavox Odyssey', 2:'Atari 2600', 3:'Intellivision',
    4:'ColecoVision', 5:'Nintendo Entertainment System', 6:'Sega Master System',
    7:'Atari 7800', 8:'TurboGrafx-16', 9:'Sega Genesis', 10:'Super Nintendo Entertainment System',
    11:'3DO Interactive Multiplayer', 12:'Sega Saturn', 13:'PlayStation (console)',
    14:'Nintendo 64', 15:'Sega Dreamcast', 16:'PlayStation 2',
    17:'Xbox (console)', 18:'Nintendo GameCube', 19:'PlayStation Portable',
    20:'Nintendo DS', 21:'Xbox 360', 22:'PlayStation 3', 23:'Wii',
    24:'PlayStation Vita', 25:'Nintendo 3DS', 26:'Xbox One', 27:'PlayStation 4',
    28:'Nintendo Switch', 29:'Xbox Series X and Series S', 30:'PlayStation 5',
},

'films': {
    1:'The Birth of a Nation', 2:'Metropolis (1927 film)', 3:'City Lights',
    4:'Nosferatu', 5:'Battleship Potemkin', 6:'Sunrise: A Song of Two Humans',
    7:'M (1931 film)', 8:'It Happened One Night', 9:'Snow White and the Seven Dwarfs (1937 film)',
    10:'The Wizard of Oz (1939 film)', 11:'Citizen Kane', 12:'Casablanca (film)',
    13:'Double Indemnity', 14:'Rome, Open City', 15:'Bicycle Thieves',
    16:'All About Eve', 17:'Rashomon', 18:'Singin\' in the Rain',
    19:'Rear Window', 20:'Pather Panchali', 21:'12 Angry Men (1957 film)',
    22:'Vertigo (film)', 23:'Breathless (1960 film)', 24:'Psycho (1960 film)',
    25:'L\'Avventura', 26:'Lawrence of Arabia (film)', 27:'8½',
    28:'The Good, the Bad and the Ugly', 29:'Rosemary\'s Baby (film)',
    30:'2001: A Space Odyssey (film)', 31:'The Godfather', 32:'Chinatown (1974 film)',
    33:'One Flew Over the Cuckoo\'s Nest (film)', 34:'Taxi Driver',
    35:'Star Wars (film)', 36:'Apocalypse Now', 37:'Raiders of the Lost Ark',
    38:'Blade Runner', 39:'E.T. the Extra-Terrestrial', 40:'Schindler\'s List',
    41:'Pulp Fiction', 42:'The Shawshank Redemption', 43:'Toy Story',
    44:'Titanic (1997 film)', 45:'The Matrix', 46:'Gladiator (2000 film)',
    47:'Spirited Away', 48:'The Lord of the Rings: The Fellowship of the Ring',
    49:'City of God (film)', 50:'No Country for Old Men', 51:'The Dark Knight',
    52:'Inception', 53:'The Social Network (film)', 54:'Gravity (2013 film)',
    55:'Boyhood (film)', 56:'Mad Max: Fury Road', 57:'Moonlight (2016 film)',
    58:'Parasite (2019 film)', 59:'Nomadland', 60:'Everything Everywhere All at Once',
},

'lunes': {
    1:'Io (moon)', 2:'Europa (moon)', 3:'Ganymede (moon)', 4:'Callisto (moon)',
    5:'Amalthea (moon)', 6:'Himalia (moon)', 7:'Elara (moon)', 8:'Pasiphae (moon)',
    9:'Sinope (moon)', 10:'Lysithea (moon)', 11:'Carme (moon)', 12:'Ananke (moon)',
    13:'Leda (moon)', 14:'Thebe (moon)', 15:'Adrastea (moon)', 16:'Metis (moon)',
    17:'Titan (moon)', 18:'Rhea (moon)', 19:'Iapetus', 20:'Dione (moon)',
    21:'Tethys (moon)', 22:'Enceladus (moon)', 23:'Mimas (moon)', 24:'Hyperion (moon)',
    25:'Phoebe (moon)', 26:'Janus (moon)', 27:'Epimetheus (moon)', 28:'Helene (moon)',
    29:'Telesto (moon)', 30:'Calypso (moon)', 31:'Atlas (moon)', 32:'Prometheus (moon)',
    33:'Pandora (moon)', 34:'Miranda (moon)', 35:'Ariel (moon)', 36:'Umbriel (moon)',
    37:'Titania (moon)', 38:'Oberon (moon)', 39:'Puck (moon)', 40:'Sycorax (moon)',
    41:'Triton (moon)', 42:'Nereid (moon)', 43:'Larissa (moon)', 44:'Proteus (moon)',
    45:'Despina (moon)', 46:'Galatea (moon)', 47:'Thalassa (moon)', 48:'Naiad (moon)',
    49:'Charon (moon)', 50:'Nix (moon)', 51:'Hydra (moon)', 52:'Kerberos (moon)',
    53:'Styx (moon)', 54:'The Moon', 55:'Phobos (moon)', 56:'Deimos (moon)',
},

'xxe': {
    1:'First World War', 2:'Second World War', 3:'Russian Revolution',
    4:'Great Depression', 5:'Cold War', 6:'Space Race', 7:'Nuclear warfare',
    8:'Decolonization', 9:'Civil rights movement', 10:'Moon landing',
    11:'Fall of the Berlin Wall', 12:'Dissolution of the Soviet Union',
    13:'Internet', 14:'September 11 attacks', 15:'Human Genome Project',
},

'musiques': {
    1:'Classical music', 2:'Opera', 3:'Jazz', 4:'Blues', 5:'Rock and roll',
    6:'Folk music', 7:'Soul music', 8:'Reggae', 9:'Funk', 10:'Punk rock',
    11:'Heavy metal music', 12:'Electronic music', 13:'Hip hop music',
    14:'Pop music', 15:'Country music',
},

'religions': {
    1:'Christianity', 2:'Islam', 3:'Judaism', 4:'Hinduism', 5:'Buddhism',
    6:'Sikhism', 7:'Taoism', 8:'Confucianism', 9:'Shinto', 10:'Zoroastrianism',
    11:'Jainism', 12:'Baha\'i Faith', 13:'Animism', 14:'Ancient Egyptian religion',
    15:'Greek mythology',
},

}

# ─── Traitement ───────────────────────────────────────────────────────────────
total_ok = total_fail = 0

for folder, entries in LIST_DATA.items():
    if folder in SKIP_FOLDERS:
        continue
    folder_path = FULL / folder
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    print(f'\n=== {folder} ({len(entries)} entrées) ===')

    for num, title in sorted(entries.items()):
        # Essayer d'abord l'image originale (full-res)
        url = get_original_url(title)
        method = 'orig'

        # Fallback : thumbnail 1200px (parfois original n'existe pas)
        if not url:
            url = get_thumb_url(title, 1200)
            method = 'thumb'

        if not url:
            print(f'  #{num} ECHEC ({title})')
            FAIL_LOG.write(f'{folder}\t{num}\t{title}\n')
            FAIL_LOG.flush()
            total_fail += 1
            continue

        try:
            w = save_full(url, folder, num)
            OK_LOG.write(f'{folder}\t{num}\t{title}\t{method}\t{w}px\n')
            OK_LOG.flush()
            total_ok += 1
        except Exception as e:
            print(f'  #{num} ERREUR ({title}): {e}')
            FAIL_LOG.write(f'{folder}\t{num}\t{title}\tERREUR:{e}\n')
            FAIL_LOG.flush()
            total_fail += 1

print(f'\n=== TERMINÉ : {total_ok} OK, {total_fail} échecs ===')
OK_LOG.close()
FAIL_LOG.close()
