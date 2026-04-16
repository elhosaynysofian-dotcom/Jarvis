#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. - Assistant Personnel Windows
Version 1.2

Nouveautés :
  - Ouvrir n'importe quelle application (Chrome, Spotify, Word...)
  - Ouvrir n'importe quel dossier (Bureau, Documents, Images...)
  - Rechercher un fichier sur le PC
  - Contrôler le volume (monter, baisser, couper)
"""

import os
import re
import glob
import ctypes
import datetime
import shutil
import subprocess
import sys

import pyttsx3
import requests
import speech_recognition as sr


# ══════════════════════════════════════════════════════════════
#  CONFIGURATION  ← modifie ici selon tes préférences
# ══════════════════════════════════════════════════════════════

VILLE_DEFAUT = "Nimes"   # Ta ville par défaut pour la météo

# Dossiers Windows courants
APPDATA    = os.environ.get("APPDATA", "")
LOCALAPP   = os.environ.get("LOCALAPPDATA", "")
MAISON     = os.path.expanduser("~")

DOSSIERS = {
    "bureau":           os.path.join(MAISON, "Desktop"),
    "documents":        os.path.join(MAISON, "Documents"),
    "images":           os.path.join(MAISON, "Pictures"),
    "photos":           os.path.join(MAISON, "Pictures"),
    "musique":          os.path.join(MAISON, "Music"),
    "vidéos":           os.path.join(MAISON, "Videos"),
    "videos":           os.path.join(MAISON, "Videos"),
    "téléchargements":  os.path.join(MAISON, "Downloads"),
    "telechargements":  os.path.join(MAISON, "Downloads"),
    "downloads":        os.path.join(MAISON, "Downloads"),
}

DOSSIER_TELECHARGEMENTS = DOSSIERS["téléchargements"]

# Applications courantes avec leurs chemins possibles
APPS = {
    "chrome": [
        os.path.join(LOCALAPP, r"Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ],
    "google chrome": [
        os.path.join(LOCALAPP, r"Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "mozilla": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ],
    "spotify": [
        os.path.join(APPDATA, r"Spotify\Spotify.exe"),
        os.path.join(LOCALAPP, r"Microsoft\WindowsApps\Spotify.exe"),
    ],
    "discord": [
        os.path.join(LOCALAPP, r"Discord\Update.exe"),
    ],
    "word": [
        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
        r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
    ],
    "excel": [
        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
    ],
    "powerpoint": [
        r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
    ],
    "notepad":       [r"C:\Windows\System32\notepad.exe"],
    "bloc-notes":    [r"C:\Windows\System32\notepad.exe"],
    "bloc notes":    [r"C:\Windows\System32\notepad.exe"],
    "calculatrice":  [r"C:\Windows\System32\calc.exe"],
    "calculette":    [r"C:\Windows\System32\calc.exe"],
    "paint":         [r"C:\Windows\System32\mspaint.exe"],
    "explorateur":   [r"C:\Windows\explorer.exe"],
    "gestionnaire des tâches": [r"C:\Windows\System32\taskmgr.exe"],
    "vlc": [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ],
    "vscode": [
        os.path.join(LOCALAPP, r"Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "visual studio code": [
        os.path.join(LOCALAPP, r"Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
    ],
    "steam": [
        r"C:\Program Files (x86)\Steam\steam.exe",
        r"C:\Program Files\Steam\steam.exe",
    ],
    "whatsapp": [
        os.path.join(LOCALAPP, r"WhatsApp\WhatsApp.exe"),
    ],
    "telegram": [
        os.path.join(APPDATA, r"Telegram Desktop\Telegram.exe"),
    ],
}

# Catégories de tri fichiers
CATEGORIES = {
    "Images":     [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".ico", ".svg", ".tiff", ".raw"],
    "Documents":  [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx",
                   ".odt", ".ods", ".odp", ".csv", ".rtf", ".md"],
    "Vidéos":     [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"],
    "Audio":      [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma", ".opus"],
    "Archives":   [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "Programmes": [".exe", ".msi", ".bat", ".cmd", ".ps1"],
    "Autres":     [],
}

# Traduction conditions météo
METEO_FR = {
    "Sunny": "ensoleillé",
    "Clear": "ciel dégagé",
    "Partly cloudy": "partiellement nuageux",
    "Cloudy": "nuageux",
    "Overcast": "couvert",
    "Mist": "brumeux",
    "Fog": "brouillard",
    "Freezing fog": "brouillard givrant",
    "Light rain": "légère pluie",
    "Moderate rain": "pluie modérée",
    "Heavy rain": "forte pluie",
    "Light snow": "légère neige",
    "Moderate snow": "neige modérée",
    "Heavy snow": "forte neige",
    "Blizzard": "blizzard",
    "Thunder": "orage",
    "Thundery outbreaks possible": "orages possibles",
    "Light rain shower": "légères averses",
    "Moderate or heavy rain shower": "averses modérées à fortes",
    "Patchy rain possible": "quelques averses possibles",
    "Patchy snow possible": "quelques flocons possibles",
    "Blowing snow": "vent de neige",
    "Light sleet": "grésil léger",
    "Moderate or heavy sleet": "grésil modéré",
}


# ══════════════════════════════════════════════════════════════
#  SYNTHÈSE VOCALE
# ══════════════════════════════════════════════════════════════

def parler(texte):
    print(f"\n  JARVIS : {texte}\n")
    moteur = pyttsx3.init()
    moteur.setProperty("rate", 155)
    moteur.setProperty("volume", 1.0)
    voices = moteur.getProperty("voices")
    for v in voices:
        if "french" in v.name.lower() or "fr_" in v.id.lower() or "hortense" in v.name.lower():
            moteur.setProperty("voice", v.id)
            break
    moteur.say(texte)
    moteur.runAndWait()
    moteur.stop()


# ══════════════════════════════════════════════════════════════
#  RECONNAISSANCE VOCALE
# ══════════════════════════════════════════════════════════════

def ecouter():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("  [ En écoute... appuie sur Ctrl+C pour quitter ]\n")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return ""
    try:
        texte = recognizer.recognize_google(audio, language="fr-FR")
        print(f"  Vous    : {texte}")
        return texte.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        parler("Je n'arrive pas à accéder à la reconnaissance vocale. Vérifie ta connexion internet.")
        return ""


# ══════════════════════════════════════════════════════════════
#  VOLUME WINDOWS
# ══════════════════════════════════════════════════════════════

def volume_haut():
    """Monte le volume de 5 crans."""
    for _ in range(5):
        ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)   # VK_VOLUME_UP
        ctypes.windll.user32.keybd_event(0xAF, 0, 2, 0)
    parler("Volume augmenté.")

def volume_bas():
    """Baisse le volume de 5 crans."""
    for _ in range(5):
        ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)   # VK_VOLUME_DOWN
        ctypes.windll.user32.keybd_event(0xAE, 0, 2, 0)
    parler("Volume baissé.")

def volume_mute():
    """Coupe ou réactive le son."""
    ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)       # VK_VOLUME_MUTE
    ctypes.windll.user32.keybd_event(0xAD, 0, 2, 0)
    parler("Son coupé.")


# ══════════════════════════════════════════════════════════════
#  APPLICATIONS
# ══════════════════════════════════════════════════════════════

def extraire_nom_app(commande):
    """Retire les mots de déclenchement pour ne garder que le nom de l'app."""
    mots = ["ouvre", "ouvrir", "lance", "lancer", "démarre", "démarrer",
            "start", "exécute", "exécuter", "jarvis"]
    resultat = commande
    for mot in mots:
        resultat = re.sub(rf'\b{mot}\b', '', resultat, flags=re.IGNORECASE)
    return resultat.strip()

def ouvrir_application(nom):
    """Tente d'ouvrir une application par son nom."""
    nom_lower = nom.lower().strip()

    # 1. Cherche dans le dictionnaire prédéfini
    if nom_lower in APPS:
        for chemin in APPS[nom_lower]:
            # Gérer les chemins avec wildcard (ex: Discord)
            chemins_trouves = glob.glob(chemin)
            cible = chemins_trouves[0] if chemins_trouves else chemin
            if os.path.exists(cible):
                subprocess.Popen([cible])
                parler(f"{nom.title()} est ouvert.")
                return

    # 2. Cherche dans le PATH Windows (commande where)
    try:
        result = subprocess.run(
            ["where", nom_lower],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            chemin = result.stdout.strip().splitlines()[0]
            subprocess.Popen([chemin])
            parler(f"{nom.title()} est ouvert.")
            return
    except Exception:
        pass

    # 3. Dernier recours : commande start de Windows
    try:
        subprocess.Popen(f'start "" "{nom_lower}"', shell=True)
        parler(f"Je lance {nom.title()}.")
        return
    except Exception:
        pass

    parler(f"Je n'ai pas trouvé {nom.title()}. Vérifie qu'il est bien installé.")


# ══════════════════════════════════════════════════════════════
#  DOSSIERS
# ══════════════════════════════════════════════════════════════

def extraire_nom_dossier(commande):
    """Extrait le nom du dossier depuis la commande."""
    mots = ["ouvre", "ouvrir", "affiche", "montre", "va", "dans",
            "le", "la", "les", "mon", "mes", "dossier", "répertoire", "jarvis"]
    resultat = commande
    for mot in mots:
        resultat = re.sub(rf'\b{mot}\b', '', resultat, flags=re.IGNORECASE)
    return resultat.strip()

def ouvrir_dossier(nom):
    """Ouvre un dossier Windows par son nom."""
    nom_lower = nom.lower().strip()

    # Cherche dans les dossiers connus
    for cle, chemin in DOSSIERS.items():
        if cle in nom_lower or nom_lower in cle:
            if os.path.exists(chemin):
                subprocess.Popen(f'explorer "{chemin}"')
                parler(f"Le dossier {cle.title()} est ouvert.")
                return
            else:
                parler(f"Le dossier {cle.title()} est introuvable sur ce PC.")
                return

    # Chemin personnalisé si l'utilisateur en donne un
    if os.path.exists(nom):
        subprocess.Popen(f'explorer "{nom}"')
        parler("Le dossier est ouvert.")
        return

    parler(f"Je ne connais pas le dossier {nom}. Tu peux me dire : bureau, documents, images, musique, vidéos ou téléchargements.")


# ══════════════════════════════════════════════════════════════
#  RECHERCHE DE FICHIERS
# ══════════════════════════════════════════════════════════════

def extraire_nom_fichier(commande):
    """Extrait le nom du fichier à chercher depuis la commande."""
    mots = ["cherche", "chercher", "trouve", "trouver", "où", "est",
            "mon", "mes", "le", "la", "les", "fichier", "document",
            "mon fichier", "jarvis"]
    resultat = commande
    for mot in mots:
        resultat = re.sub(rf'\b{mot}\b', '', resultat, flags=re.IGNORECASE)
    return resultat.strip()

def chercher_fichier(nom):
    """Cherche un fichier dans les dossiers courants et annonce le résultat."""
    if not nom:
        parler("Quel fichier dois-je chercher ?")
        return

    parler(f"Je cherche {nom} sur ton PC. Un instant.")

    lieux = [
        MAISON,
        os.path.join(MAISON, "Desktop"),
        os.path.join(MAISON, "Documents"),
        os.path.join(MAISON, "Downloads"),
        os.path.join(MAISON, "Pictures"),
        os.path.join(MAISON, "Videos"),
        os.path.join(MAISON, "Music"),
    ]

    resultats = []
    for lieu in lieux:
        if not os.path.exists(lieu):
            continue
        try:
            for racine, _, fichiers in os.walk(lieu):
                for f in fichiers:
                    if nom.lower() in f.lower():
                        resultats.append(os.path.join(racine, f))
                if len(resultats) >= 5:
                    break
        except PermissionError:
            continue
        if len(resultats) >= 5:
            break

    if not resultats:
        parler(f"Je n'ai pas trouvé de fichier contenant {nom} dans tes dossiers.")
        return

    if len(resultats) == 1:
        chemin = resultats[0]
        parler(f"J'ai trouvé un fichier : {os.path.basename(chemin)}.")
        print(f"  → {chemin}")
        # Ouvre le dossier contenant le fichier
        subprocess.Popen(f'explorer /select,"{chemin}"')
    else:
        noms = ", ".join(os.path.basename(r) for r in resultats[:3])
        parler(f"J'ai trouvé {len(resultats)} fichiers. Les premiers : {noms}.")
        print("  Résultats :")
        for r in resultats:
            print(f"  → {r}")
        # Ouvre le dossier du premier résultat
        subprocess.Popen(f'explorer /select,"{resultats[0]}"')


# ══════════════════════════════════════════════════════════════
#  HEURE / DATE / MÉTÉO / ACCUEIL
# ══════════════════════════════════════════════════════════════

def donner_heure():
    now = datetime.datetime.now()
    parler(f"Il est actuellement {now.strftime('%Hh%M')}.")

def donner_date():
    JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    MOIS  = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    now = datetime.datetime.now()
    parler(f"Nous sommes le {JOURS[now.weekday()]} {now.day} {MOIS[now.month - 1]} {now.year}.")

def extraire_ville(commande):
    match = re.search(
        r'\b(?:à|a|sur|pour|de)\s+([a-zàâäéèêëîïôùûüç][a-zàâäéèêëîïôùûüç\s\-]{1,30}?)(?:\s*\?|$)',
        commande
    )
    if match:
        return match.group(1).strip().title()
    match = re.search(
        r'(?:météo|meteo|temps|température|temperature)\s+([a-zàâäéèêëîïôùûüç][a-zàâäéèêëîïôùûüç\s\-]{1,30}?)(?:\s*\?|$)',
        commande
    )
    if match:
        candidat = match.group(1).strip()
        if candidat not in ("aujourd", "aujourd hui", "il", "fait", "il fait"):
            return candidat.title()
    return VILLE_DEFAUT

def donner_meteo(ville=VILLE_DEFAUT):
    try:
        url = f"https://wttr.in/{ville}?format=j1"
        response = requests.get(url, timeout=6)
        response.raise_for_status()
        data = response.json()
        cond     = data["current_condition"][0]
        temp     = cond["temp_C"]
        ressenti = cond["FeelsLikeC"]
        desc_en  = cond["weatherDesc"][0]["value"]
        desc_fr  = METEO_FR.get(desc_en, desc_en)
        parler(f"À {ville}, il fait actuellement {temp} degrés, ressenti {ressenti} degrés. {desc_fr}.")
    except requests.exceptions.ConnectionError:
        parler("Je ne peux pas accéder à la météo. Vérifie ta connexion internet.")
    except requests.exceptions.Timeout:
        parler("La météo met trop de temps à répondre. Réessaie dans un instant.")
    except Exception as e:
        print(f"  [ERREUR météo] {e}")
        parler(f"Je n'ai pas pu récupérer la météo de {ville}.")

def mode_accueil():
    JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    MOIS  = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    now = datetime.datetime.now()
    parler(f"Bienvenue de retour. Il est {now.strftime('%Hh%M')}, nous sommes le {JOURS[now.weekday()]} {now.day} {MOIS[now.month - 1]} {now.year}.")
    try:
        url = f"https://wttr.in/{VILLE_DEFAUT}?format=j1"
        data = requests.get(url, timeout=4).json()
        cond    = data["current_condition"][0]
        temp    = cond["temp_C"]
        desc_fr = METEO_FR.get(cond["weatherDesc"][0]["value"], cond["weatherDesc"][0]["value"])
        parler(f"À {VILLE_DEFAUT}, il fait {temp} degrés, {desc_fr}.")
    except Exception:
        pass
    parler("Tous les systèmes sont prêts. Que puis-je faire pour toi ?")


# ══════════════════════════════════════════════════════════════
#  TRI TÉLÉCHARGEMENTS
# ══════════════════════════════════════════════════════════════

def trier_telechargements():
    if not os.path.exists(DOSSIER_TELECHARGEMENTS):
        parler("Le dossier Téléchargements est introuvable.")
        return
    fichiers = [f for f in os.listdir(DOSSIER_TELECHARGEMENTS)
                if os.path.isfile(os.path.join(DOSSIER_TELECHARGEMENTS, f))]
    if not fichiers:
        parler("Le dossier Téléchargements ne contient aucun fichier à trier.")
        return
    parler(f"J'ai trouvé {len(fichiers)} fichiers. Je les classe par catégories sans rien supprimer.")
    deplaces, stats, erreurs = 0, {}, 0
    for fichier in fichiers:
        _, ext = os.path.splitext(fichier)
        ext = ext.lower()
        categorie = "Autres"
        for cat, extensions in CATEGORIES.items():
            if ext in extensions:
                categorie = cat
                break
        dossier_cible = os.path.join(DOSSIER_TELECHARGEMENTS, categorie)
        os.makedirs(dossier_cible, exist_ok=True)
        src = os.path.join(DOSSIER_TELECHARGEMENTS, fichier)
        dst = os.path.join(dossier_cible, fichier)
        if os.path.exists(dst):
            base, extension = os.path.splitext(fichier)
            compteur = 1
            while os.path.exists(dst):
                dst = os.path.join(dossier_cible, f"{base}_copie{compteur}{extension}")
                compteur += 1
        try:
            shutil.move(src, dst)
            deplaces += 1
            stats[categorie] = stats.get(categorie, 0) + 1
        except Exception as e:
            print(f"  [ERREUR] {fichier} : {e}")
            erreurs += 1
    if stats:
        details = ", ".join(f"{v} en {k}" for k, v in stats.items())
        parler(f"C'est fait. {deplaces} fichiers classés : {details}.")
    if erreurs:
        parler(f"Attention : {erreurs} fichiers n'ont pas pu être déplacés.")


# ══════════════════════════════════════════════════════════════
#  INTERPRÉTATION DES COMMANDES
# ══════════════════════════════════════════════════════════════

def interpreter(commande):
    if not commande:
        return True

    # ── Quitter ───────────────────────────────────────────────
    if any(mot in commande for mot in
           ["au revoir", "ferme", "quitte", "arrête", "stop jarvis",
            "bonne nuit", "à bientôt", "c'est tout"]):
        parler("À bientôt.")
        return False

    # ── Mode accueil ──────────────────────────────────────────
    elif any(mot in commande for mot in
             ["je suis rentré", "je suis à la maison", "je suis arrivé",
              "mode accueil", "bonjour jarvis", "bonsoir jarvis"]):
        mode_accueil()

    # ── Heure ─────────────────────────────────────────────────
    elif any(mot in commande for mot in
             ["quelle heure", "heure est-il", "heure il est",
              "il est quelle heure", "donne l'heure", "l'heure"]):
        donner_heure()

    # ── Date ──────────────────────────────────────────────────
    elif any(mot in commande for mot in
             ["quelle date", "quel jour", "on est quel", "la date",
              "date d'aujourd", "c'est quoi le jour"]):
        donner_date()

    # ── Météo ─────────────────────────────────────────────────
    elif any(mot in commande for mot in
             ["météo", "meteo", "quel temps", "temps fait-il", "temps il fait",
              "il fait quel temps", "température", "temperature"]):
        donner_meteo(extraire_ville(commande))

    # ── Volume ────────────────────────────────────────────────
    elif any(mot in commande for mot in
             ["monte le volume", "volume plus", "plus fort", "augmente le volume"]):
        volume_haut()

    elif any(mot in commande for mot in
             ["baisse le volume", "volume moins", "moins fort", "diminue le volume"]):
        volume_bas()

    elif any(mot in commande for mot in
             ["coupe le son", "sourdine", "mute", "silence", "coupe le volume"]):
        volume_mute()

    # ── Recherche de fichier ──────────────────────────────────
    elif any(mot in commande for mot in
             ["cherche", "trouve mon fichier", "où est mon fichier",
              "trouve le fichier", "cherche le fichier"]):
        nom = extraire_nom_fichier(commande)
        chercher_fichier(nom)

    # ── Tri téléchargements ───────────────────────────────────
    elif any(mot in commande for mot in
             ["trie", "trier", "range", "classe", "organise", "nettoie"]):
        trier_telechargements()

    # ── Ouvrir un dossier ─────────────────────────────────────
    elif any(mot in commande for mot in
             ["ouvre le dossier", "ouvre mon dossier", "ouvre mes documents",
              "ouvre mes images", "ouvre mes vidéos", "ouvre ma musique",
              "ouvre le bureau", "ouvre mes téléchargements",
              "téléchargements", "téléchargement"]) and \
         any(d in commande for d in DOSSIERS.keys()):
        nom = extraire_nom_dossier(commande)
        ouvrir_dossier(nom)

    # ── Ouvrir une application ────────────────────────────────
    elif any(mot in commande for mot in ["ouvre", "lance", "démarre", "start"]):
        nom = extraire_nom_app(commande)
        if nom:
            ouvrir_application(nom)
        else:
            parler("Quelle application dois-je ouvrir ?")

    # ── Commande non reconnue ─────────────────────────────────
    else:
        parler("Je n'ai pas encore cette capacité. Tu peux me demander : l'heure, la date, la météo, d'ouvrir une application ou un dossier, de chercher un fichier, ou de contrôler le volume.")

    return True


# ══════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  J.A.R.V.I.S. — Assistant Personnel Windows v1.2")
    print("=" * 60)
    print("  Commandes disponibles :")
    print("    → Heure / Date / Météo")
    print("    → Ouvre Chrome / Lance Spotify / Démarre Word")
    print("    → Ouvre le dossier Documents / Images / Bureau")
    print("    → Cherche mon fichier [nom]")
    print("    → Monte le volume / Baisse le volume / Coupe le son")
    print("    → Trie les téléchargements")
    print("    → Je suis rentré / Au revoir")
    print("=" * 60 + "\n")

    parler("Systèmes en ligne. Bonjour, je suis JARVIS. Comment puis-je t'aider ?")

    actif = True
    while actif:
        try:
            commande = ecouter()
            actif = interpreter(commande)
        except KeyboardInterrupt:
            print("\n")
            parler("Arrêt demandé. À bientôt.")
            break

    print("\n  [ JARVIS arrêté ]\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
