"""
Architectes : BÂTIMENTS uniquement (pas de portraits).
Image = œuvre la plus emblématique de l'architecte.
"""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, save_both

FOLDER = 'architectes_majeurs'

# (num, name, most_famous_building_wiki_title)
ARCHITECTES = [
    (1,  'Brunelleschi',      'Florence Cathedral'),          # Dôme de Florence
    (2,  'Palladio',          'Villa La Rotonda'),            # Villa Rotonda
    (3,  'Gaudí',             'Sagrada Família'),             # La Sagrada Família
    (4,  'Frank Lloyd Wright','Fallingwater'),                # Fallingwater
    (5,  'Le Corbusier',      'Villa Savoye'),                # Villa Savoye
    (6,  'Mies van der Rohe', 'Barcelona Pavilion'),         # Pavillon de Barcelone
    (7,  'Zaha Hadid',        'Heydar Aliyev Center'),        # Centre Heydar Aliyev
    (8,  'I. M. Pei',         'Louvre Pyramid'),              # Pyramide du Louvre
    (9,  'Michelangelo',      'St. Peter\'s Basilica'),       # Saint-Pierre de Rome
    (10, 'Christopher Wren',  'St Paul\'s Cathedral'),        # St Paul's London
    (11, 'Balthasar Neumann', 'Basilica of the Fourteen Holy Helpers'), # Vierzehnheiligen
    (12, 'Charles Garnier',   'Palais Garnier'),              # Opéra de Paris
    (13, 'Victor Horta',      'Hôtel Tassel'),               # Art nouveau Bruxelles
    (14, 'Walter Gropius',    'Bauhaus Dessau'),              # Bauhaus
    (15, 'Alvar Aalto',       'Finlandia Hall'),             # Finlandia
    (16, 'Oscar Niemeyer',    'National Congress of Brazil'), # Congrès Brésil
    (17, 'Louis Kahn',        'Salk Institute for Biological Studies'), # Salk Institute
    (18, 'Renzo Piano',       'Centre Georges Pompidou'),    # Beaubourg
    (19, 'Norman Foster',     'The Gherkin'),                # 30 St Mary Axe
    (20, 'Frank Gehry',       'Guggenheim Museum Bilbao'),   # Guggenheim Bilbao
    (21, 'Tadao Ando',        'Church of the Light'),        # Église de la Lumière
    (22, 'Jean Nouvel',       'Institut du monde arabe'),    # IMA Paris
    (23, 'Rem Koolhaas',      'CCTV headquarters'),          # CCTV Building
    (24, 'Santiago Calatrava','City of Arts and Sciences'),  # Valence
    (25, 'Herzog & de Meuron','Bird\'s Nest'),               # Stade olympique Pékin
    (26, 'Kengo Kuma',        'Japan National Stadium'),     # Stade Tokyo
    (27, 'Dominique Perrault','Bibliothèque nationale de France'), # BnF
    (28, 'Carlo Scarpa',      'Museo di Castelvecchio'),     # Castelvecchio
    (29, 'Richard Rogers',    'Lloyd\'s building'),          # Lloyd's of London
    (30, 'Bjarke Ingels',     '8 House'),                    # 8 House Copenhagen
]

ok = 0
for num, name, title in ARCHITECTES:
    print(f'#{num} {name}')
    url = get_thumb_url(title, size=800)
    if url and save_both(url, FOLDER, num, name):
        ok += 1
    else:
        print(f'  ECHEC')

print(f'\nDone: {ok}/{len(ARCHITECTES)}')
