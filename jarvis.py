#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. - Assistant Personnel Windows
Version 1.1

Nouveautés :
  - Météo en temps réel (wttr.in, sans clé API)
  - Détection automatique de la ville dans la commande
  - Reconnaissance des commandes élargie et plus naturelle
  - Mode accueil enrichi avec la météo
"""

import os
import re
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

DOSSIER_TELECHARGEMENTS = os.path.join(os.path.expanduser("~"), "Downloads")
VILLE_DEFAUT = "Nimes"   # Ta ville par défaut pour la météo

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

# Traduction des conditions météo anglaises → françaises
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
#  MOTEUR DE SYNTHÈSE VOCALE
# ══════════════════════════════════════════════════════════════

def init_tts():
    moteur = pyttsx3.init()
    moteur.setProperty("rate", 155)
    moteur.setProperty("volume", 1.0)
    voices = moteur.getProperty("voices")
    for v in voices:
        if "french" in v.name.lower() or "fr_" in v.id.lower() or "hortense" in v.name.lower():
            moteur.setProperty("voice", v.id)
            break
    return moteur


TTS = init_tts()


def parler(texte: str):
    print(f"\n  JARVIS : {texte}\n")
    TTS.say(texte)
    TTS.runAndWait()


# ══════════════════════════════════════════════════════════════
#  RECONNAISSANCE VOCALE
# ══════════════════════════════════════════════════════════════

def ecouter() -> str:
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
    except sr.RequestError as e:
        parler("Je n'arrive pas à accéder à la reconnaissance vocale. Vérifie ta connexion internet.")
        print(f"  [ERREUR] Reconnaissance vocale : {e}")
        return ""


# ══════════════════════════════════════════════════════════════
#  ACTIONS
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


def extraire_ville(commande: str) -> str:
    """
    Tente d'extraire une ville depuis la commande vocale.
    Exemples : "météo à Paris", "quel temps à Lyon", "météo Marseille".
    Retourne VILLE_DEFAUT si aucune ville n'est trouvée.
    """
    # Cherche "à <ville>" ou "sur <ville>"
    match = re.search(
        r'\b(?:à|a|sur|pour|de)\s+([a-zàâäéèêëîïôùûüç][a-zàâäéèêëîïôùûüç\s\-]{1,30}?)(?:\s*\?|$)',
        commande
    )
    if match:
        return match.group(1).strip().title()

    # Cherche "météo <ville>" ou "temps <ville>" sans préposition
    match = re.search(
        r'(?:météo|meteo|temps|température|temperature)\s+([a-zàâäéèêëîïôùûüç][a-zàâäéèêëîïôùûüç\s\-]{1,30}?)(?:\s*\?|$)',
        commande
    )
    if match:
        candidat = match.group(1).strip()
        # Ignorer les mots parasites courants
        if candidat not in ("aujourd", "aujourd hui", "il", "fait", "il fait"):
            return candidat.title()

    return VILLE_DEFAUT


def donner_meteo(ville: str = VILLE_DEFAUT):
    """
    Récupère la météo via wttr.in (gratuit, sans clé API).
    Annonce température, ressenti et condition.
    """
    try:
        url = f"https://wttr.in/{ville}?format=j1"
        response = requests.get(url, timeout=6)
        response.raise_for_status()
        data = response.json()

        cond      = data["current_condition"][0]
        temp      = cond["temp_C"]
        ressenti  = cond["FeelsLikeC"]
        desc_en   = cond["weatherDesc"][0]["value"]
        desc_fr   = METEO_FR.get(desc_en, desc_en)   # Traduit si dispo

        parler(
            f"À {ville}, il fait actuellement {temp} degrés, "
            f"ressenti {ressenti} degrés. Conditions : {desc_fr}."
        )

    except requests.exceptions.ConnectionError:
        parler("Je ne peux pas accéder à la météo. Vérifie ta connexion internet.")
    except requests.exceptions.Timeout:
        parler("La météo met trop de temps à répondre. Réessaie dans un instant.")
    except Exception as e:
        print(f"  [ERREUR météo] {e}")
        parler(f"Je n'ai pas pu récupérer la météo de {ville}.")


def ouvrir_telechargements():
    if os.path.exists(DOSSIER_TELECHARGEMENTS):
        subprocess.Popen(f'explorer "{DOSSIER_TELECHARGEMENTS}"')
        parler("Le dossier Téléchargements est ouvert.")
    else:
        parler("Je n'ai pas trouvé le dossier Téléchargements sur ce PC.")


def trier_telechargements():
    if not os.path.exists(DOSSIER_TELECHARGEMENTS):
        parler("Le dossier Téléchargements est introuvable.")
        return

    fichiers = [
        f for f in os.listdir(DOSSIER_TELECHARGEMENTS)
        if os.path.isfile(os.path.join(DOSSIER_TELECHARGEMENTS, f))
    ]

    if not fichiers:
        parler("Le dossier Téléchargements ne contient aucun fichier à trier.")
        return

    parler(
        f"J'ai trouvé {len(fichiers)} fichier{'s' if len(fichiers) > 1 else ''}. "
        "Je vais les classer par catégories. Aucun fichier ne sera supprimé."
    )

    deplaces = 0
    stats: dict[str, int] = {}
    erreurs = 0

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
            print(f"  [ERREUR] Impossible de déplacer {fichier} : {e}")
            erreurs += 1

    if stats:
        details = ", ".join(f"{v} en {k}" for k, v in stats.items())
        parler(f"C'est fait. {deplaces} fichier{'s' if deplaces > 1 else ''} classé{'s' if deplaces > 1 else ''} : {details}.")
    if erreurs:
        parler(f"Attention : {erreurs} fichier{'s' if erreurs > 1 else ''} n'ont pas pu être déplacé{'s' if erreurs > 1 else ''}.")


def mode_accueil():
    JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    MOIS  = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    now = datetime.datetime.now()
    heure_str = now.strftime("%Hh%M")
    date_str  = f"{JOURS[now.weekday()]} {now.day} {MOIS[now.month - 1]} {now.year}"

    parler(f"Bienvenue de retour. Il est {heure_str}, nous sommes le {date_str}.")

    # Météo en bonus si disponible
    try:
        url = f"https://wttr.in/{VILLE_DEFAUT}?format=j1"
        response = requests.get(url, timeout=4)
        data = response.json()
        cond    = data["current_condition"][0]
        temp    = cond["temp_C"]
        desc_en = cond["weatherDesc"][0]["value"]
        desc_fr = METEO_FR.get(desc_en, desc_en)
        parler(f"À {VILLE_DEFAUT}, il fait {temp} degrés, {desc_fr}.")
    except Exception:
        pass  # Si la météo échoue, on continue sans elle

    parler("Tous les systèmes sont prêts. Que puis-je faire pour toi ?")


# ══════════════════════════════════════════════════════════════
#  INTERPRÉTATION DES COMMANDES
# ══════════════════════════════════════════════════════════════

def interpreter(commande: str) -> bool:
    """
    Analyse la commande vocale et déclenche l'action correspondante.
    Retourne False pour quitter, True pour continuer.
    """
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
              "mode accueil", "bonjour jarvis", "bonsoir jarvis", "bienvenue"]):
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
              "il fait quel temps", "température", "temperature",
              "il fait chaud", "il fait froid"]):
        ville = extraire_ville(commande)
        donner_meteo(ville)

    # ── Tri des Téléchargements ───────────────────────────────
    elif any(mot in commande for mot in
             ["trie", "trier", "range", "ranges", "classe", "organise",
              "nettoie", "clean"]):
        trier_telechargements()

    # ── Ouvrir Téléchargements ────────────────────────────────
    elif any(mot in commande for mot in
             ["téléchargements", "téléchargement", "downloads", "ouvre les téléchargements"]):
        ouvrir_telechargements()

    # ── Commande non reconnue ─────────────────────────────────
    else:
        parler("Je n'ai pas encore cette capacité. Dis-moi l'heure, la date, la météo, ou de gérer tes téléchargements.")

    return True


# ══════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 58)
    print("  J.A.R.V.I.S. — Assistant Personnel Windows v1.1")
    print("=" * 58)
    print("  Commandes disponibles :")
    print("    → Heure / Date / Météo")
    print("    → Ouvre les téléchargements / Trie les téléchargements")
    print("    → Je suis rentré (mode accueil)")
    print("    → Au revoir (quitter)")
    print("=" * 58 + "\n")

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
