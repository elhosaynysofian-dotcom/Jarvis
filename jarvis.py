#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. - Assistant Personnel Windows
Version 1.0

Fonctionnalités :
  - Commande vocale (microphone)
  - Réponse vocale (synthèse)
  - Heure et date
  - Ouverture du dossier Téléchargements
  - Tri automatique des fichiers par catégorie
"""

import os
import datetime
import shutil
import subprocess
import sys

import pyttsx3
import speech_recognition as sr


# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

# Chemin vers le dossier Téléchargements (Windows)
DOSSIER_TELECHARGEMENTS = os.path.join(os.path.expanduser("~"), "Downloads")

# Catégories de tri et extensions associées
CATEGORIES = {
    "Images":     [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".ico", ".svg", ".tiff", ".raw"],
    "Documents":  [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx",
                   ".odt", ".ods", ".odp", ".csv", ".rtf", ".md"],
    "Vidéos":     [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"],
    "Audio":      [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma", ".opus"],
    "Archives":   [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "Programmes": [".exe", ".msi", ".bat", ".cmd", ".ps1"],
    "Autres":     [],  # Tout ce qui ne correspond à aucune catégorie ci-dessus
}


# ══════════════════════════════════════════════════════════════
#  MOTEUR DE SYNTHÈSE VOCALE
# ══════════════════════════════════════════════════════════════

def init_tts():
    """Initialise le moteur de synthèse vocale (pyttsx3)."""
    moteur = pyttsx3.init()
    moteur.setProperty("rate", 155)      # Vitesse de parole (mots/min)
    moteur.setProperty("volume", 1.0)    # Volume (0.0 à 1.0)

    # Cherche une voix française si disponible sur le système
    voices = moteur.getProperty("voices")
    for v in voices:
        if "french" in v.name.lower() or "fr_" in v.id.lower() or "hortense" in v.name.lower():
            moteur.setProperty("voice", v.id)
            break

    return moteur


# Initialisation unique au démarrage
TTS = init_tts()


def parler(texte: str):
    """Fait parler JARVIS à voix haute et affiche le texte."""
    print(f"\n  JARVIS : {texte}\n")
    TTS.say(texte)
    TTS.runAndWait()


# ══════════════════════════════════════════════════════════════
#  RECONNAISSANCE VOCALE
# ══════════════════════════════════════════════════════════════

def ecouter() -> str:
    """
    Écoute le microphone et retourne le texte reconnu.
    Utilise Google Speech Recognition (nécessite internet).
    Retourne une chaîne vide si rien n'est compris.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("  [ En écoute... appuie sur Ctrl+C pour quitter ]\n")
        # Calibration rapide du bruit ambiant
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            # Silence trop long : on recommence simplement
            return ""

    try:
        texte = recognizer.recognize_google(audio, language="fr-FR")
        print(f"  Vous    : {texte}")
        return texte.lower()

    except sr.UnknownValueError:
        # Rien de compréhensible capté
        return ""

    except sr.RequestError as e:
        parler("Je n'arrive pas à accéder à la reconnaissance vocale. Vérifie ta connexion internet.")
        print(f"  [ERREUR] Reconnaissance vocale : {e}")
        return ""


# ══════════════════════════════════════════════════════════════
#  ACTIONS
# ══════════════════════════════════════════════════════════════

def donner_heure():
    """Annonce l'heure actuelle."""
    now = datetime.datetime.now()
    heure_str = now.strftime("%Hh%M")
    parler(f"Il est actuellement {heure_str}.")


def donner_date():
    """Annonce la date complète du jour."""
    JOURS  = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    MOIS   = ["janvier", "février", "mars", "avril", "mai", "juin",
               "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    now = datetime.datetime.now()
    parler(
        f"Nous sommes le {JOURS[now.weekday()]} "
        f"{now.day} {MOIS[now.month - 1]} {now.year}."
    )


def ouvrir_telechargements():
    """Ouvre le dossier Téléchargements dans l'Explorateur Windows."""
    if os.path.exists(DOSSIER_TELECHARGEMENTS):
        subprocess.Popen(f'explorer "{DOSSIER_TELECHARGEMENTS}"')
        parler("Le dossier Téléchargements est ouvert.")
    else:
        parler("Je n'ai pas trouvé le dossier Téléchargements sur ce PC.")


def trier_telechargements():
    """
    Trie les fichiers du dossier Téléchargements par catégorie.
    Crée des sous-dossiers : Images, Documents, Vidéos, Audio, Archives, Programmes, Autres.
    Ne supprime rien. En cas de doublon, renomme le fichier avec le suffixe _copie.
    """
    if not os.path.exists(DOSSIER_TELECHARGEMENTS):
        parler("Le dossier Téléchargements est introuvable.")
        return

    # Lister uniquement les fichiers (pas les sous-dossiers)
    fichiers = [
        f for f in os.listdir(DOSSIER_TELECHARGEMENTS)
        if os.path.isfile(os.path.join(DOSSIER_TELECHARGEMENTS, f))
    ]

    if not fichiers:
        parler("Le dossier Téléchargements ne contient aucun fichier à trier.")
        return

    parler(
        f"J'ai trouvé {len(fichiers)} fichier{'s' if len(fichiers) > 1 else ''}. "
        "Je vais les classer par catégories. Aucun fichier ne sera supprimé. C'est parti."
    )

    deplaces = 0
    stats: dict[str, int] = {}
    erreurs = 0

    for fichier in fichiers:
        _, ext = os.path.splitext(fichier)
        ext = ext.lower()

        # Déterminer la catégorie
        categorie = "Autres"
        for cat, extensions in CATEGORIES.items():
            if ext in extensions:
                categorie = cat
                break

        # Créer le sous-dossier si nécessaire
        dossier_cible = os.path.join(DOSSIER_TELECHARGEMENTS, categorie)
        os.makedirs(dossier_cible, exist_ok=True)

        src = os.path.join(DOSSIER_TELECHARGEMENTS, fichier)
        dst = os.path.join(dossier_cible, fichier)

        # Gérer les doublons : ajouter _copie avant l'extension
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

    # Résumé vocal
    if stats:
        details = ", ".join(f"{v} en {k}" for k, v in stats.items())
        parler(f"C'est fait. {deplaces} fichier{'s' if deplaces > 1 else ''} classé{'s' if deplaces > 1 else ''} : {details}.")
    if erreurs:
        parler(f"Attention : {erreurs} fichier{'s' if erreurs > 1 else ''} n'ont pas pu être déplacé{'s' if erreurs > 1 else ''}, car ils étaient probablement ouverts.")


def mode_accueil():
    """Active le mode accueil quand l'utilisateur rentre chez lui."""
    JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    MOIS  = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    now = datetime.datetime.now()
    heure_str  = now.strftime("%Hh%M")
    date_str   = f"{JOURS[now.weekday()]} {now.day} {MOIS[now.month - 1]} {now.year}"

    parler(
        f"Bienvenue de retour. "
        f"Il est {heure_str}, nous sommes le {date_str}. "
        "Tous les systèmes sont prêts. Que puis-je faire pour toi ?"
    )


# ══════════════════════════════════════════════════════════════
#  INTERPRÉTATION DES COMMANDES
# ══════════════════════════════════════════════════════════════

def interpreter(commande: str) -> bool:
    """
    Analyse la commande vocale et déclenche l'action correspondante.
    Retourne False si l'utilisateur souhaite quitter, True sinon.
    """
    if not commande:
        return True

    # ── Quitter ───────────────────────────────────────────────
    if any(mot in commande for mot in ["au revoir", "ferme", "quitte", "arrête", "stop jarvis", "bonne nuit"]):
        parler("À bientôt.")
        return False

    # ── Mode accueil ──────────────────────────────────────────
    elif any(mot in commande for mot in
             ["je suis rentré", "je suis à la maison", "mode accueil", "bonjour jarvis",
              "bonsoir jarvis", "bienvenue"]):
        mode_accueil()

    # ── Heure ─────────────────────────────────────────────────
    elif any(mot in commande for mot in ["quelle heure", "heure est-il", "heure il est", "donne l'heure", "l'heure"]):
        donner_heure()

    # ── Date ──────────────────────────────────────────────────
    elif any(mot in commande for mot in ["quelle date", "quel jour", "on est quel", "la date", "date d'aujourd"]):
        donner_date()

    # ── Tri des Téléchargements ───────────────────────────────
    elif any(mot in commande for mot in ["trie", "trier", "range", "ranges", "classe", "organise"]):
        trier_telechargements()

    # ── Ouvrir Téléchargements ────────────────────────────────
    elif any(mot in commande for mot in ["téléchargements", "téléchargement", "downloads"]):
        ouvrir_telechargements()

    # ── Commande non reconnue ─────────────────────────────────
    else:
        parler("Je n'ai pas compris. Peux-tu reformuler ?")

    return True


# ══════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

def main():
    """Démarre JARVIS en boucle d'écoute."""
    print("=" * 55)
    print("  J.A.R.V.I.S. — Assistant Personnel Windows v1.0")
    print("=" * 55)
    print("  Dis 'au revoir' ou appuie sur Ctrl+C pour quitter.\n")

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
