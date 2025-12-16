# API Radio Madagascar

## Overview
API Flask pour scraper dynamiquement les informations des radios malgaches depuis radio.mg et fournir les URLs de flux audio MP3 en direct.

## Endpoints

### GET /
Retourne les informations sur l'API et les radios disponibles.

### GET /ecouter?radio=<nom_radio>
Retourne les informations d'une radio specifique avec l'URL du flux MP3.

Exemple: `/ecouter?radio=donbosco`

Reponse:
```json
{
    "radio": "donbosco",
    "nom": "Radio Don Bosco",
    "frequence": "93.4 FM",
    "stream_url": "https://stream.zeno.fm/9ar8ggfsks8uv",
    "type": "MP3 en ligne directe",
    "format": "audio/mpeg",
    "statut": "en_ligne"
}
```

### GET /radios
Liste toutes les radios disponibles.

## Radios Disponibles
- donbosco - Radio Don Bosco (93.4 FM)
- alefamusic - Alefa Music
- fahazavana - Radio Fahazavana
- mariamadagascar - Radio Maria Madagascar

## Structure du Projet
```
main.py          - Application Flask principale
requirements.txt - Dependances Python
```

## Technologies
- Python 3.11
- Flask
- BeautifulSoup4 (scraping)
- Requests

## Comment Ecouter
Utilisez l'URL `stream_url` retournee par l'API dans n'importe quel lecteur audio compatible MP3:
- VLC Media Player
- Navigateur web (balise <audio>)
- Applications mobiles
