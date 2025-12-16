from flask import Flask, jsonify, request, render_template_string
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

PLAYER_HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Radio Don Bosco - Madagascar</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        .player-container {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        .radio-logo {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(45deg, #e94560, #0f3460);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 40px;
        }
        h1 { font-size: 24px; margin-bottom: 10px; }
        .frequency { color: #e94560; font-size: 18px; margin-bottom: 20px; }
        .status { 
            display: inline-block;
            padding: 5px 15px;
            background: #27ae60;
            border-radius: 20px;
            font-size: 12px;
            margin-bottom: 20px;
        }
        .status.offline { background: #e74c3c; }
        audio {
            width: 100%;
            margin: 20px 0;
        }
        .play-btn {
            background: #e94560;
            border: none;
            color: white;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 30px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .play-btn:hover { transform: scale(1.05); }
        .play-btn:disabled { background: #666; cursor: not-allowed; }
        .info { margin-top: 20px; font-size: 14px; opacity: 0.7; }
        .radios-list {
            margin-top: 30px;
            text-align: left;
        }
        .radios-list a {
            display: block;
            color: #e94560;
            text-decoration: none;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
    </style>
</head>
<body>
    <div class="player-container">
        <div class="radio-logo">{{ radio_emoji }}</div>
        <h1>{{ nom }}</h1>
        <p class="frequency">{{ frequence or 'FM Madagascar' }}</p>
        <span class="status">EN DIRECT</span>
        
        <audio id="radioPlayer" controls>
            <source src="{{ stream_url }}" type="audio/mpeg">
            Votre navigateur ne supporte pas l'audio.
        </audio>
        
        <button class="play-btn" onclick="togglePlay()">Ecouter</button>
        
        <p class="info">Cliquez sur le bouton ou utilisez les controles audio</p>
        
        <div class="radios-list">
            <p style="opacity: 0.5; margin-bottom: 10px;">Autres radios:</p>
            {% for r in autres_radios %}
            <a href="/player?radio={{ r }}">{{ r|title }}</a>
            {% endfor %}
        </div>
    </div>
    
    <script>
        const audio = document.getElementById('radioPlayer');
        const btn = document.querySelector('.play-btn');
        
        function togglePlay() {
            if (audio.paused) {
                audio.play();
                btn.textContent = 'Pause';
            } else {
                audio.pause();
                btn.textContent = 'Ecouter';
            }
        }
        
        audio.onplay = () => btn.textContent = 'Pause';
        audio.onpause = () => btn.textContent = 'Ecouter';
    </script>
</body>
</html>
'''

RADIOS = {
    "donbosco": {"url": "https://radio.mg/don-bosco/", "slug": "don-bosco", "name": "Radio Don Bosco", "frequency": "93.4 FM"},
    "alefamusic": {"url": "https://radio.mg/alefamusic/", "slug": "alefamusic", "name": "Alefa Music", "frequency": None},
    "fahazavana": {"url": "https://radio.mg/fahazavana/", "slug": "fahazavana", "name": "Radio Fahazavana", "frequency": None},
    "mariamadagascar": {"url": "https://radio.mg/maria-madagascar/", "slug": "maria-madagascar", "name": "Radio Maria Madagascar", "frequency": None},
    "alliance92": {"url": "https://radio.mg/alliance-92/", "slug": "alliance-92", "name": "Alliance 92", "frequency": "92 FM"},
    "anikristy": {"url": "https://radio.mg/an-i-kristy/", "slug": "an-i-kristy", "name": "An'i Kristy", "frequency": None},
    "dagosound": {"url": "https://radio.mg/dago-sound/", "slug": "dago-sound", "name": "Dago Sound", "frequency": None},
    "fmfoi": {"url": "https://radio.mg/fmfoi/", "slug": "fmfoi", "name": "FM Foi", "frequency": None},
    "freefm": {"url": "https://radio.mg/free-fm-104-2/", "slug": "free-fm-104-2", "name": "Free FM 104.2", "frequency": "104.2 FM"},
    "hopefy": {"url": "https://radio.mg/hopefy/", "slug": "hopefy", "name": "Hopefy", "frequency": None},
    "joyradioafrica": {"url": "https://radio.mg/joy-radio-africa/", "slug": "joy-radio-africa", "name": "Joy Radio Africa", "frequency": None},
    "mbs": {"url": "https://radio.mg/mbs/", "slug": "mbs", "name": "MBS Radio", "frequency": None},
    "netprotv": {"url": "https://radio.mg/netpro-tv/", "slug": "netpro-tv", "name": "NetPro.TV Radio", "frequency": None},
    "olivasoa": {"url": "https://radio.mg/olivasoa/", "slug": "olivasoa", "name": "Olivasoa Radio", "frequency": None},
    "anjomara": {"url": "https://radio.mg/radio-anjomara/", "slug": "radio-anjomara", "name": "Radio Anjomara", "frequency": None},
    "bitsika": {"url": "https://radio.mg/bitsika/", "slug": "bitsika", "name": "Radio Bitsika", "frequency": None},
    "fanambarana": {"url": "https://radio.mg/fanambarana/", "slug": "fanambarana", "name": "Radio Fanambarana", "frequency": None},
    "feonny": {"url": "https://radio.mg/feon-ny/", "slug": "feon-ny", "name": "Radio Feon'ny", "frequency": None},
    "fivoarana": {"url": "https://radio.mg/fivoarana/", "slug": "fivoarana", "name": "Radio Fivoarana", "frequency": None},
    "mtv": {"url": "https://radio.mg/mtv/", "slug": "mtv", "name": "Radio MTV", "frequency": None},
    "paradisagasy": {"url": "https://radio.mg/paradisagasy/", "slug": "paradisagasy", "name": "Radio Paradisagasy", "frequency": None},
    "rmk": {"url": "https://radio.mg/madagasikara-hoan-i-kristy/", "slug": "madagasikara-hoan-i-kristy", "name": "Radio Madagasikara Hoan'i Kristy", "frequency": None},
    "vaovaomahasoa": {"url": "https://radio.mg/vaovao-mahasoa/", "slug": "vaovao-mahasoa", "name": "Radio Vaovao Mahasoa", "frequency": None},
    "vazogasy": {"url": "https://radio.mg/vazo-gasy/", "slug": "vazo-gasy", "name": "Radio Vazogasy", "frequency": None},
    "rdj": {"url": "https://radio.mg/des-jeunes-fm/", "slug": "des-jeunes-fm", "name": "RDJ - Radio Des Jeunes", "frequency": None},
    "rnasava102": {"url": "https://radio.mg/rna-sava102/", "slug": "rna-sava102", "name": "RNA Sava 102 FM", "frequency": "102 FM"},
    "rna": {"url": "https://radio.mg/rna/", "slug": "rna", "name": "RNA Webradio", "frequency": None},
    "siokafm": {"url": "https://radio.mg/sioka-fm-106/", "slug": "sioka-fm-106", "name": "Sioka FM 106", "frequency": "106 FM"},
    "soaimadagasikara": {"url": "https://radio.mg/soa-i-madagasikara/", "slug": "soa-i-madagasikara", "name": "Soa i Madagasikara", "frequency": None},
    "taratra": {"url": "https://radio.mg/taratra-105-6-fm/", "slug": "taratra-105-6-fm", "name": "Taratra 105.6 FM", "frequency": "105.6 FM"},
    "tiakobe": {"url": "https://radio.mg/tiako-be/", "slug": "tiako-be", "name": "Tiako Be", "frequency": None},
    "vahiniala": {"url": "https://radio.mg/vahiniala/", "slug": "vahiniala", "name": "Vahiniala", "frequency": None},
}

def scrape_all_radios_from_site():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        response = requests.get("https://radio.mg/", headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'lxml')
        radios = []
        links = soup.find_all('a', href=True)
        seen = set()
        for link in links:
            href = link.get('href', '')
            if 'radio.mg/' in href and not href.endswith('#') and 'gadona' not in href:
                match = re.search(r'radio\.mg/([a-zA-Z0-9\-]+)/?$', href)
                if match:
                    slug = match.group(1)
                    if slug not in seen and slug not in ['manifest.json', 'favorites', 'dmca', 'fitanana-ny-tsiambaratelo', 'hampiditra-ny-onjam-peonao', 'fanampiana', 'vao-nihaino', 'gadon-kira']:
                        seen.add(slug)
                        name = link.get_text(strip=True) or slug.replace('-', ' ').title()
                        radios.append({
                            "id": slug.replace('-', ''),
                            "slug": slug,
                            "name": name if name else slug.replace('-', ' ').title(),
                            "url": f"https://radio.mg/{slug}/"
                        })
        return radios
    except:
        return []

def get_stream_url_from_zeno(zeno_slug):
    if not zeno_slug:
        return None
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        zeno_url = f"https://zeno.fm/radio/{zeno_slug}/"
        response = requests.get(zeno_url, headers=headers, timeout=10)
        
        stream_match = re.search(r'stream\.zeno\.fm/([a-zA-Z0-9]+)', response.text)
        if stream_match:
            return f"https://stream.zeno.fm/{stream_match.group(1)}"
    except:
        pass
    
    return None

def scrape_radio_info_from_page(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        info = {
            "name": None,
            "frequency": None,
            "logo": None,
            "stream_url": None,
            "current_track": None,
            "current_artist": None
        }
        
        h1_tag = soup.find('h1')
        if h1_tag:
            info["name"] = h1_tag.get_text(strip=True)
        
        h2_tag = soup.find('h2')
        if h2_tag:
            info["frequency"] = h2_tag.get_text(strip=True)
        
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            if 'logo' in src.lower() or 'radio' in str(img.get('alt', '')).lower():
                info["logo"] = src
                break
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                stream_match = re.search(r'stream\.zeno\.fm/([a-zA-Z0-9]+)', script.string)
                if stream_match:
                    info["stream_url"] = f"https://stream.zeno.fm/{stream_match.group(1)}"
                    break
                
                patterns = [
                    r'"stream_url"\s*:\s*"([^"]+)"',
                    r'"url"\s*:\s*"(https?://[^"]+(?:\.mp3|stream)[^"]*)"',
                    r'src:\s*["\']([^"\']+(?:\.mp3|stream)[^"\']*)["\']',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, script.string, re.IGNORECASE)
                    if matches:
                        info["stream_url"] = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        break
                if info["stream_url"]:
                    break
        
        return info
    except:
        return None

def scrape_radio_info(radio_key):
    if radio_key not in RADIOS:
        return None
    
    radio_config = RADIOS[radio_key]
    url = radio_config["url"]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
    }
    
    page_info = scrape_radio_info_from_page(url, headers)
    
    name = radio_config.get("name")
    frequency = radio_config.get("frequency")
    logo_url = None
    stream_url = None
    
    if page_info:
        name = page_info.get("name") or name
        frequency = page_info.get("frequency") or frequency
        logo_url = page_info.get("logo")
        stream_url = page_info.get("stream_url")
    
    if not stream_url and radio_config.get("zeno_slug"):
        stream_url = get_stream_url_from_zeno(radio_config["zeno_slug"])
    
    if not stream_url:
        stream_url = f"https://listen.instant.audio/?r=radio-mg/{radio_config['slug']}"
    
    return {
        "radio": radio_key,
        "nom": name,
        "frequence": frequency,
        "logo": logo_url,
        "type": "MP3 en ligne directe",
        "stream_url": stream_url,
        "site_source": url,
        "statut": "en_ligne",
        "format": "audio/mpeg",
        "instructions": "Utilisez l'URL stream_url pour ecouter la radio en direct dans un lecteur audio"
    }

@app.route('/')
def index():
    return jsonify({
        "message": "API Radio Madagascar",
        "description": "API pour ecouter les radios malgaches en ligne",
        "endpoints": {
            "ecouter": "GET /ecouter?radio=<nom_radio> - Obtenir les infos JSON d'une radio",
            "radios": "GET /radios - Liste simple des radios",
            "radios_all": "GET /radios/all - Liste complete avec stream_url (plus lent)",
            "radios_scrape": "GET /radios/scrape - Scraper radio.mg en direct",
            "player": "GET /player?radio=<nom_radio> - Lecteur audio HTML"
        },
        "radios_disponibles": list(RADIOS.keys()),
        "total_radios": len(RADIOS),
        "exemple": "/ecouter?radio=donbosco"
    })

@app.route('/ecouter')
def ecouter():
    radio = request.args.get('radio', '').lower().strip()
    
    if not radio:
        return jsonify({
            "erreur": "Parametre 'radio' manquant",
            "radios_disponibles": list(RADIOS.keys()),
            "exemple": "/ecouter?radio=donbosco"
        }), 400
    
    radio_info = scrape_radio_info(radio)
    
    if radio_info is None:
        return jsonify({
            "erreur": f"Radio '{radio}' non trouvee",
            "radios_disponibles": list(RADIOS.keys())
        }), 404
    
    return jsonify(radio_info)

@app.route('/radios')
def liste_radios():
    radios_list = []
    for key, config in RADIOS.items():
        radios_list.append({
            "id": key,
            "nom": config.get("name"),
            "frequence": config.get("frequency"),
            "url_site": config.get("url"),
            "url_api": f"/ecouter?radio={key}",
            "url_player": f"/player?radio={key}"
        })
    
    return jsonify({
        "radios_disponibles": radios_list,
        "total": len(RADIOS)
    })

@app.route('/radios/all')
def liste_radios_complete():
    radios_list = []
    for key, config in RADIOS.items():
        radio_info = scrape_radio_info(key)
        if radio_info:
            radios_list.append(radio_info)
    
    return jsonify({
        "radios": radios_list,
        "total": len(radios_list)
    })

@app.route('/radios/scrape')
def scrape_radios_live():
    radios = scrape_all_radios_from_site()
    return jsonify({
        "radios_trouvees": radios,
        "total": len(radios),
        "source": "https://radio.mg/"
    })

@app.route('/player')
def player():
    radio = request.args.get('radio', 'donbosco').lower().strip()
    
    if radio not in RADIOS:
        radio = 'donbosco'
    
    radio_info = scrape_radio_info(radio)
    
    autres_radios = [k for k in RADIOS.keys() if k != radio]
    
    return render_template_string(PLAYER_HTML,
        nom=radio_info.get('nom', 'Radio Madagascar'),
        frequence=radio_info.get('frequence'),
        stream_url=radio_info.get('stream_url'),
        radio_emoji='📻',
        autres_radios=autres_radios
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
