#!/usr/bin/env python3
"""Télécharge les images manquantes avec des termes alternatifs, génère SVG sinon."""
import pathlib, requests, subprocess, sys, json, re, time, textwrap
from PIL import Image
import io

REPO   = pathlib.Path(__file__).parent.parent
THUMBS = REPO / 'thumbs'
CACHE  = pathlib.Path(__file__).parent / '.cache.pkl'

# (liste, n, nom_principal, [termes_alternatifs], couleur_fallback)
MISSING = [
    ('civilisations',        '25', 'Empire moghol',       ['Mughal Empire', 'Shah Jahan', 'Taj Mahal'], '#8B5CF6'),
    ('compositeurs',         '36', 'Henry Purcell',        ['Henry Purcell composer', 'Purcell Dido Aeneas'], '#3B82F6'),
    ('constellations',       '23', 'Centaure',             ['Centaurus constellation', 'Alpha Centauri star'], '#1D4ED8'),
    ('constellations',       '34', 'Éridain',              ['Eridanus constellation', 'Achernar star'], '#1D4ED8'),
    ('grands_scientifiques', '16', 'Johannes Kepler',      ['Kepler astronomer portrait', 'Johannes Kepler'], '#059669'),
    ('grands_scientifiques', '38', 'James Watson',         ['James Watson biologist DNA', 'James Dewey Watson'], '#059669'),
    ('grandes_explorations', '16', 'Samuel de Champlain',  ['Samuel de Champlain explorer', 'Champlain New France'], '#D97706'),
    ('grandes_explorations', '18', 'Mungo Park',           ['Mungo Park explorer Africa', 'Mungo Park Niger'], '#D97706'),
    ('grandes_explorations', '25', 'Valentina Teréchkova', ['Valentina Tereshkova cosmonaut', 'Tereshkova Vostok'], '#D97706'),
    ('parcs_nationaux',      '8',  'Kakadu',               ['Kakadu National Park', 'Kakadu Australia wetlands'], '#16A34A'),
    ('architectes_majeurs',  '16', 'Oscar Niemeyer',       ['Oscar Niemeyer architect', 'Niemeyer Brasilia'], '#DC2626'),
    ('architectes_majeurs',  '17', 'Louis Kahn',           ['Louis Kahn architect', 'Kahn Salk Institute'], '#DC2626'),
    ('architectes_majeurs',  '24', 'Santiago Calatrava',   ['Santiago Calatrava architect', 'Calatrava bridge'], '#DC2626'),
    ('architectes_majeurs',  '27', 'Dominique Perrault',   ['Dominique Perrault architect', 'Perrault Bibliotheque France'], '#DC2626'),
    ('architectes_majeurs',  '28', 'Carlo Scarpa',         ['Carlo Scarpa architect', 'Scarpa Brion Cemetery'], '#DC2626'),
    ('architectes_majeurs',  '29', 'Richard Rogers',       ['Richard Rogers architect', 'Centre Pompidou Rogers Piano'], '#DC2626'),
]

HEADERS = {'User-Agent': 'MemoApp/1.0 (educational; contact@example.com)'}

def search_wikipedia_image(terms):
    for term in terms:
        url = 'https://en.wikipedia.org/w/api.php'
        params = {
            'action': 'query', 'format': 'json', 'prop': 'pageimages',
            'piprop': 'thumbnail', 'pithumbsize': 400,
            'titles': term, 'redirects': 1,
        }
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=10)
            pages = r.json().get('query', {}).get('pages', {})
            for page in pages.values():
                thumb = page.get('thumbnail', {}).get('source')
                if thumb:
                    return thumb
        except Exception:
            pass
        # Also try search
        sparams = {
            'action': 'query', 'format': 'json', 'list': 'search',
            'srsearch': term, 'srlimit': 1,
        }
        try:
            r = requests.get(url, params=sparams, headers=HEADERS, timeout=10)
            results = r.json().get('query', {}).get('search', [])
            if results:
                title = results[0]['title']
                p2 = {'action':'query','format':'json','prop':'pageimages',
                      'piprop':'thumbnail','pithumbsize':400,'titles':title}
                r2 = requests.get(url, params=p2, headers=HEADERS, timeout=10)
                pages2 = r2.json().get('query',{}).get('pages',{})
                for page in pages2.values():
                    thumb = page.get('thumbnail',{}).get('source')
                    if thumb:
                        return thumb
        except Exception:
            pass
        time.sleep(0.3)
    return None

def make_svg_fallback(name, color):
    initials = ''.join(w[0].upper() for w in name.split()[:2] if w)
    lines = textwrap.wrap(name, 14)
    label_y = 85 + (len(lines) - 1) * -8
    text_els = ''.join(
        f'<text x="60" y="{label_y + i*16}" font-size="10" fill="white" '
        f'text-anchor="middle" font-family="sans-serif">{l}</text>'
        for i, l in enumerate(lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 90">
  <rect width="120" height="90" fill="{color}" rx="4"/>
  <circle cx="60" cy="34" r="22" fill="rgba(255,255,255,0.2)"/>
  <text x="60" y="41" font-size="18" fill="white" text-anchor="middle"
        font-family="sans-serif" font-weight="bold">{initials}</text>
  {text_els}
</svg>'''

def svg_to_webp(svg_str, out_path, size=(200, 150)):
    """Convert SVG to WebP via cairosvg or PIL with solid color fallback."""
    try:
        import cairosvg
        png_data = cairosvg.svg2png(bytestring=svg_str.encode(), output_width=size[0], output_height=size[1])
        img = Image.open(io.BytesIO(png_data)).convert('RGB')
        img.save(out_path, 'WEBP', quality=85)
        return True
    except ImportError:
        pass
    # Fallback: solid color WebP
    color_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', svg_str)
    hex_color = color_match.group(1) if color_match else '#6B7280'
    r, g, b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
    img = Image.new('RGB', size, (r, g, b))
    img.save(out_path, 'WEBP', quality=85)
    return True

def download_image(url, out_path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert('RGB')
            img = img.resize((200, 150), Image.LANCZOS)
            img.save(out_path, 'WEBP', quality=85)
            return True
    except Exception as e:
        print(f'    ✗ download error: {e}')
    return False

if __name__ == '__main__':
    ok = 0
    fallback = 0
    for lst, n, name, alts, color in MISSING:
        out = THUMBS / lst / f'{n}.webp'
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            print(f'  ✓ {lst}/{n} déjà présent')
            ok += 1
            continue
        print(f'  ▶ {lst}/{n} — {name}')
        url = search_wikipedia_image([name] + alts)
        if url:
            if download_image(url, out):
                print(f'    ✓ téléchargé depuis Wikipedia')
                ok += 1
                continue
        # SVG fallback
        svg = make_svg_fallback(name, color)
        svg_to_webp(svg, out)
        print(f'    ~ SVG fallback généré')
        fallback += 1
    print(f'\n✓ {ok} téléchargés, {fallback} fallbacks SVG')
