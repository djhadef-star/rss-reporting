import os
import re
import unicodedata
from datetime import datetime
from urllib.parse import urlparse
import feedparser
import pandas as pd

# -----------------------------
# 1. Définition des flux RSS
# -----------------------------
RSS_FEEDS = [
    "https://www.frandroid.com/feed",
    "https://www.phonandroid.com/feed",
    "https://www.clubic.com/feed",
    "https://www.01net.com/feed",
]

# -----------------------------
# 2. Définition des catégories
# -----------------------------
CATEGORIES = {
    "SMARTPHONE": [
        "smartphone", "phone", "pixel", "forfait", "android", "ios", "5g", "6g", "reseau", "esim", "wifi",
        "routeur", "netgear", "ethernet", "traceur", "tag", "lunette", "casque vr"
    ],
    "PC": ["pc", "geekom", "framework", "windows"],
    "PERIPHERIQUE": [
        "clavier", "ecran", "souris", "imprimante", "logitech", "corsair", "steam deck", "chargeur",
        "charge", "batterie externe", "upgreen", "branche", "ssd", "lexar", "serveur", "nas", "peripherique"
    ],
    "TABLETTE": [
        "tablette", "fold", "pad", "note", "kindle", "remarkable", "liseuse", "kobo", "ebooks", "pliable",
        "pliure", "pli"
    ],
    "LOGICIELS_OS": [
        "logiciels", "software", "windows", "power toys", "office", "microsoft", "linux", "bios", "os",
        "mail", "rss", "slack", "teams", "capture", "outlook", "gmail", "drive", "cleaner", "vpn",
        "traduction", "chat", "automatisation", "edge", "chrome", "safari", "firefox", "opera", "vivaldi",
        "moteur de recherche"
    ],
    "IA": [
        "ia", "ai", "intelligence artificielle", "token", "anthropic", "open ai", "chat gpt", "gemini",
        "meta", "claude", "openclaw", "perplexity", "prompt", "copilot", "siri"
    ],
    "VIDEO": [
        "iptv", "netflix", "canal", "tf1", "tv", "omni", "pics", "vlc", "videos", "editeur", "cinema", "3d",
        "plex", "televiseur", "televiseurs", "lg", "hdmi", "rgb", "videoprojecteur", "awol", "xgimi",
        "jmgo", "stick", "dji", "osmo", "insta360", "cast"
    ],
    "AUDIO": [
        "casque", "audio", "pods", "buds", "headphone", "jbl", "shockz", "clip", "ecouteurs",
        "reduction de bruit", "enceinte", "barre de son", "harman"
    ],
    "MOBILITE_DOUCE": [
        "mobilite", "velo", "trottinette", "cargo", "pliable", "pliant", "sacoche", "antivol", "vae",
        "navigo", "blablacar", "taxi", "rer", "transport en commun"
    ],
    "VOITURE": [
        "voiture", "automobile", "conduite", "conduire", "rouler", "essence", "carburant", "monospace",
        "berline", "citadine", "suv", "permis", "km", "volkswagen", "mercedes", "bmw", "byd", "mg", "renault",
        "peugeot", "toyota", "nissan", "stellantis", "citroen", "dacia", "kia", "fiat", "tesla", "ford", "jeep",
        "twingo", "autonome", "fsd", "waze", "google maps", "auto", "carplay", "taxe", "moto"
    ],
    "MENAGE": [
        "aspirateur", "dyson", "roborock", "narwal", "mova", "ecovacs", "dreame", "tineco", "shark", "laveur",
        "lavage", "machine a laver", "vitres", "pressing", "defroisseur", "centrale vapeur", "fer a repasser",
        "tambour", "maison", "linge", "vaisselle", "lave vaisselle"
    ],
    "CUISINE": [
        "airfryer", "ninja", "moulinex", "coffee", "delonghi", "tefal", "cuisine", "plaque", "four",
        "cafetiere", "cafe", "expresso", "barbecue", "kenwood", "soda", "agrume", "frigo", "refrigerateur",
        "congelateur", "plante", "jardin"
    ],
    "MAISON": [
        "solaire", "electricite", "compteur", "gaz", "energie", "edf", "solar", "starlink", "box", "hue",
        "ikea", "robot", "freebox", "livebox", "home", "matter", "fibre", "camera", "surveillance", "serrure",
        "nuki", "sonnette", "keypad", "cle"
    ],
    "EXTERIEUR_SANTE_SPORT": [
        "sante", "fitbit", "bracelet", "circa", "montre", "watch", "sommeil", "dormir", "ondes", "withings",
        "peau", "sport", "course", "natation", "coros", "coach", "outdoor", "garmin", "polar", "amazfit",
        "suunto", "muscle", "musculation", "randonnee", "band", "whoop"
    ],
    "LUDIQUE": [
        "jeux", "ludique", "jeux de societe", "jeux video", "enfant", "cinema", "film", "switch",
        "playstation", "xbox", "manette"
    ],
    "ACTU_JUR_POL": [
        "ue", "cnil", "souverainete", "europe", "chine", "russie", "iran", "condamne", "gafam",
        "conseil d etat", "arcom", "rgpd", "ia act", "bruxelles", "union europeenne", "otan", "proces",
        "plaintes", "regles", "reglementation", "loi", "juge", "justice", "tribunal", "sanction", "dsa",
        "politique", "onu", "france", "etat", "trump", "commission europeenne", "geopolitique",
        "diplomatie", "cyberattaque", "piratage", "taxe", "presidentielle"
    ],
    "ACTU_ECO": [
        "depense", "bourse", "milliards", "vente", "rachat", "capitalisation", "acquisition", "argent",
        "opa", "fusion", "bulle", "usine", "production", "productivite", "salaires", "crise", "energie",
        "rente", "rentable", "perte", "benefice", "chiffre d affaires", "comptable", "penurie"
    ]
}

# -----------------------------
# 3. Fonctions utilitaires
# -----------------------------
def normalize(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    return text.lower()

# Normalisation préalable unique des mots-clés
NORM_CATEGORIES = {
    cat: [normalize(kw) for kw in keywords]
    for cat, keywords in CATEGORIES.items()
}

def extract_source(url):
    domain = urlparse(url).netloc.lower()
    for source in ["frandroid", "phonandroid", "clubic", "01net"]:
        if source in domain:
            return source.capitalize()
    return domain

def categorize(title, description):
    text = normalize(f"{title} {description}")
    for category, keywords in NORM_CATEGORIES.items():
        for kw in keywords:
            # Recherche du mot entier pour éviter les faux positifs (ex: "ia", "pc")
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text):
                return category
    return "NON_CLASSE"

# -----------------------------
# 4. Collecte RSS
# -----------------------------
articles = []

for feed in RSS_FEEDS:
    parsed = feedparser.parse(feed)
    for entry in parsed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        description = entry.get("summary", "")

        # Extraction fiable de la date via feedparser
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_dt = datetime(*entry.published_parsed[:6])
        else:
            published_dt = datetime.now()

        category = categorize(title, description)
        source = extract_source(link)

        articles.append({
            "source": source,
            "date": published_dt,
            "titre": title,
            "lien": link,
            "categorie": category
        })

# -----------------------------
# 5. Traitement Pandas & Export
# -----------------------------
df = pd.DataFrame(articles)

if not df.empty:
    # Tri par date décroissante
    df = df.sort_values(by="date", ascending=False)
    # Formatage de la date en texte pour le CSV
    df["date"] = df["date"].dt.strftime("%d/%m/%Y %H:%M")

# Création du dossier 'output' s'il n'existe pas
os.makedirs("output", exist_ok=True)

# Exportation en CSV sécurisée (lisible sous Excel)
df.to_csv("output/rss_history.csv", index=False, sep=";", encoding="utf-8-sig")

print("Collecte terminée ! Fichier généré dans output/rss_history.csv")