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
    "donbosco": {
        "url": "https://radio.mg/don-bosco/",
        "slug": "don-bosco",
        "zeno_slug": "radio-don-bosco-madagascar",
        "name": "Radio Don Bosco",
        "frequency": "93.4 FM"
    },
    "alefamusic": {
        "url": "https://radio.mg/alefamusic/",
        "slug": "alefamusic",
        "zeno_slug": None,
        "name": "Alefa Music",
        "frequency": None
    },
    "fahazavana": {
        "url": "https://radio.mg/fahazavana/",
        "slug": "fahazavana",
        "zeno_slug": None,
        "name": "Radio Fahazavana",
        "frequency": None
    },
    "mariamadagascar": {
        "url": "https://radio.mg/maria-madagascar/",
        "slug": "maria-madagascar",
        "zeno_slug": None,
        "name": "Radio Maria Madagascar",
        "frequency": None
    }
}

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
            "ecouter": "GET /ecouter?radio=<nom_radio>",
            "radios": "GET /radios"
        },
        "radios_disponibles": list(RADIOS.keys()),
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
            "url_api": f"/ecouter?radio={key}"
        })
    
    return jsonify({
        "radios_disponibles": radios_list,
        "total": len(RADIOS)
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
