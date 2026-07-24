"""Corrections finales des cas difficiles."""
import sys
sys.path.insert(0, r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\build')
sys.stdout.reconfigure(encoding='utf-8')
from lib_img import get_thumb_url, get_file_url, save_both

# Renzo Piano → The Shard (London) ou MAXXI Rome
print('Architectes #18 Renzo Piano')
for t in ['The Shard', 'MAXXI', 'Whitney Museum of American Art (2015)']:
    url = get_thumb_url(t, size=800)
    if url:
        save_both(url, 'architectes_majeurs', 18, 'Renzo Piano')
        break

# Musée Pompidou → essai avec file direct
print('Musée #10 Pompidou')
for t in ['Centre Georges Pompidou', 'Pompidou Center', 'Pompidou']:
    url = get_thumb_url(t, size=800)
    if url:
        save_both(url, 'musees_monde', 10, 'Pompidou')
        break

# Quai Branly → Jean Nouvel architecture
print('Musée #21 Quai Branly')
url = get_file_url('File:Quai-branly.jpg', size=800)
if not url:
    for t in ['Quai Branly–Jacques Chirac museum', 'Jean Nouvel']:
        url = get_thumb_url(t, size=800)
        if url:
            break
if url:
    save_both(url, 'musees_monde', 21, 'Quai Branly')

# Nairobi National Museum
print('Musée #23 Nairobi')
for t in ['Nairobi National Museum', 'Kenya National Museum']:
    url = get_thumb_url(t, size=800)
    if url:
        save_both(url, 'musees_monde', 23, 'Nairobi')
        break

# Constellation Cocher (Auriga) → file direct du starfield
print('Constellation #29 Cocher/Auriga')
url = get_file_url('File:Auriga_constellation_map.png', size=800)
if not url:
    url = get_file_url('File:AurigaCC.jpg', size=800)
if not url:
    # Capella est l'étoile principale, use a photo of Auriga from stellarium or similar
    url = get_thumb_url('Capella', size=800)
if url:
    save_both(url, 'constellations', 29, 'Cocher')

# Découvertes #4 Alphabet
print('Découvertes #4 Alphabet')
for t in ['History of the alphabet', 'Greek alphabet', 'Phoenician']:
    url = get_thumb_url(t, size=800)
    if url:
        save_both(url, 'decouvertes_scientifiques', 4, 'Alphabet')
        break

# Découvertes #30 IA
print('Découvertes #30 IA')
for t in ['Artificial intelligence', 'GPT-4', 'DALL-E']:
    url = get_thumb_url(t, size=800)
    if url:
        save_both(url, 'decouvertes_scientifiques', 30, 'IA')
        break

print('\nDone.')
