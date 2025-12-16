from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

RADIOS = {
    "donbosco": {"url": "https://radio.mg/don-bosco/", "slug": "don-bosco", "name": "Radio Don Bosco", "frequency": "93.4 FM", "zeno_slug": "radio-don-bosco-madagascar"},
    "alefamusic": {"url": "https://radio.mg/alefamusic/", "slug": "alefamusic", "name": "Alefa Music", "frequency": None, "zeno_slug": "alefamusic"},
    "fahazavana": {"url": "https://radio.mg/fahazavana/", "slug": "fahazavana", "name": "Radio Fahazavana", "frequency": None, "zeno_slug": "radio-fahazavana"},
    "mariamadagascar": {"url": "https://radio.mg/maria-madagascar/", "slug": "maria-madagascar", "name": "Radio Maria Madagascar", "frequency": None, "zeno_slug": "radio-maria-madagascar"},
    "alliance92": {"url": "https://radio.mg/alliance-92/", "slug": "alliance-92", "name": "Alliance 92", "frequency": "92 FM", "zeno_slug": "alliance-92"},
    "anikristy": {"url": "https://radio.mg/an-i-kristy/", "slug": "an-i-kristy", "name": "An'i Kristy", "frequency": None, "zeno_slug": "an-i-kristy"},
    "dagosound": {"url": "https://radio.mg/dago-sound/", "slug": "dago-sound", "name": "Dago Sound", "frequency": None, "zeno_slug": "dago-sound"},
    "fmfoi": {"url": "https://radio.mg/fmfoi/", "slug": "fmfoi", "name": "FM Foi", "frequency": None, "zeno_slug": "fmfoi"},
    "freefm": {"url": "https://radio.mg/free-fm-104-2/", "slug": "free-fm-104-2", "name": "Free FM 104.2", "frequency": "104.2 FM", "zeno_slug": "free-fm-104-2"},
    "hopefy": {"url": "https://radio.mg/hopefy/", "slug": "hopefy", "name": "Hopefy", "frequency": None, "zeno_slug": "hopefy"},
    "joyradioafrica": {"url": "https://radio.mg/joy-radio-africa/", "slug": "joy-radio-africa", "name": "Joy Radio Africa", "frequency": None, "zeno_slug": "joy-radio-africa"},
    "mbs": {"url": "https://radio.mg/mbs/", "slug": "mbs", "name": "MBS Radio", "frequency": None, "zeno_slug": "mbs-radio"},
    "netprotv": {"url": "https://radio.mg/netpro-tv/", "slug": "netpro-tv", "name": "NetPro.TV Radio", "frequency": None, "zeno_slug": "netpro-tv-radio"},
    "olivasoa": {"url": "https://radio.mg/olivasoa/", "slug": "olivasoa", "name": "Olivasoa Radio", "frequency": None, "zeno_slug": "olivasoa-radio"},
    "anjomara": {"url": "https://radio.mg/radio-anjomara/", "slug": "radio-anjomara", "name": "Radio Anjomara", "frequency": None, "zeno_slug": "radio-anjomara"},
    "bitsika": {"url": "https://radio.mg/bitsika/", "slug": "bitsika", "name": "Radio Bitsika", "frequency": None, "zeno_slug": "radio-bitsika"},
    "fanambarana": {"url": "https://radio.mg/fanambarana/", "slug": "fanambarana", "name": "Radio Fanambarana", "frequency": None, "zeno_slug": "radio-fanambarana"},
    "feonny": {"url": "https://radio.mg/feon-ny/", "slug": "feon-ny", "name": "Radio Feon'ny", "frequency": None, "zeno_slug": "radio-feon-ny"},
    "fivoarana": {"url": "https://radio.mg/fivoarana/", "slug": "fivoarana", "name": "Radio Fivoarana", "frequency": None, "zeno_slug": "radio-fivoarana"},
    "mtv": {"url": "https://radio.mg/mtv/", "slug": "mtv", "name": "Radio MTV", "frequency": None, "zeno_slug": "radio-mtv-madagascar"},
    "paradisagasy": {"url": "https://radio.mg/paradisagasy/", "slug": "paradisagasy", "name": "Radio Paradisagasy", "frequency": None, "zeno_slug": "radio-paradisagasy"},
    "rmk": {"url": "https://radio.mg/madagasikara-hoan-i-kristy/", "slug": "madagasikara-hoan-i-kristy", "name": "Radio Madagasikara Hoan'i Kristy", "frequency": None, "zeno_slug": "radio-madagasikara-hoan-i-kristy"},
    "vaovaomahasoa": {"url": "https://radio.mg/vaovao-mahasoa/", "slug": "vaovao-mahasoa", "name": "Radio Vaovao Mahasoa", "frequency": None, "zeno_slug": "radio-vaovao-mahasoa"},
    "vazogasy": {"url": "https://radio.mg/vazo-gasy/", "slug": "vazo-gasy", "name": "Radio Vazogasy", "frequency": None, "zeno_slug": "radio-vazo-gasy"},
    "rdj": {"url": "https://radio.mg/des-jeunes-fm/", "slug": "des-jeunes-fm", "name": "RDJ - Radio Des Jeunes", "frequency": None, "zeno_slug": "rdj-radio-des-jeunes"},
    "rnasava102": {"url": "https://radio.mg/rna-sava102/", "slug": "rna-sava102", "name": "RNA Sava 102 FM", "frequency": "102 FM", "zeno_slug": "rna-sava-102-fm"},
    "rna": {"url": "https://radio.mg/rna/", "slug": "rna", "name": "RNA Webradio", "frequency": None, "zeno_slug": "rna-webradio"},
    "siokafm": {"url": "https://radio.mg/sioka-fm-106/", "slug": "sioka-fm-106", "name": "Sioka FM 106", "frequency": "106 FM", "zeno_slug": "sioka-fm-106"},
    "soaimadagasikara": {"url": "https://radio.mg/soa-i-madagasikara/", "slug": "soa-i-madagasikara", "name": "Soa i Madagasikara", "frequency": None, "zeno_slug": "soa-i-madagasikara"},
    "taratra": {"url": "https://radio.mg/taratra-105-6-fm/", "slug": "taratra-105-6-fm", "name": "Taratra 105.6 FM", "frequency": "105.6 FM", "zeno_slug": "taratra-105-6-fm"},
    "tiakobe": {"url": "https://radio.mg/tiako-be/", "slug": "tiako-be", "name": "Tiako Be", "frequency": None, "zeno_slug": "tiako-be"},
    "vahiniala": {"url": "https://radio.mg/vahiniala/", "slug": "vahiniala", "name": "Vahiniala", "frequency": None, "zeno_slug": "vahiniala"},
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
        stream_url = f"https://zeno.fm/radio/{radio_config.get('zeno_slug', radio_config['slug'])}/"
    
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
            "player": "GET /player?radio=<nom_radio> - Obtenir les infos JSON d'une radio",
            "radios": "GET /radios - Liste simple des radios",
            "radios_all": "GET /radios/all - Liste complete avec stream_url (plus lent)",
            "radios_scrape": "GET /radios/scrape - Scraper radio.mg en direct"
        },
        "radios_disponibles": list(RADIOS.keys()),
        "total_radios": len(RADIOS),
        "exemple": "/player?radio=freefm"
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
        return jsonify({
            "erreur": f"Radio '{radio}' non trouvee",
            "radios_disponibles": list(RADIOS.keys())
        }), 404
    
    radio_info = scrape_radio_info(radio)
    
    if radio_info is None:
        return jsonify({
            "erreur": f"Impossible de recuperer les infos pour '{radio}'",
            "radios_disponibles": list(RADIOS.keys())
        }), 500
    
    return jsonify(radio_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
