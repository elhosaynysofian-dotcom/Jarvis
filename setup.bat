@echo off
chcp 65001 >nul
title JARVIS - Installation et demarrage

echo.
echo  =====================================================
echo   J.A.R.V.I.S. -- Installation des dependances
echo  =====================================================
echo.

:: Verifier que Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERREUR] Python n'est pas installe ou pas dans le PATH.
    echo.
    echo  Installe Python depuis : https://www.python.org/downloads/
    echo  Important : coche "Add Python to PATH" lors de l'installation.
    echo.
    pause
    exit /b 1
)

echo  Python detecte. Installation des librairies...
echo.

:: Mettre a jour pip
python -m pip install --upgrade pip --quiet

:: Installer pyttsx3 et SpeechRecognition
pip install pyttsx3 SpeechRecognition

:: Tenter d'installer PyAudio directement
echo.
echo  Installation de PyAudio...
pip install pyaudio
if errorlevel 1 (
    echo.
    echo  Installation directe echouee. Tentative via pipwin...
    pip install pipwin
    pipwin install pyaudio
    if errorlevel 1 (
        echo.
        echo  [ATTENTION] PyAudio n'a pas pu etre installe automatiquement.
        echo.
        echo  Solution manuelle :
        echo    1. Va sur : https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
        echo    2. Telecharge le fichier .whl correspondant a ta version Python
        echo       (ex: PyAudio-0.2.14-cp311-cp311-win_amd64.whl pour Python 3.11 64-bit)
        echo    3. Ouvre un terminal dans ce dossier et tape :
        echo       pip install PyAudio-0.2.14-cp311-cp311-win_amd64.whl
        echo.
        pause
        exit /b 1
    )
)

echo.
echo  =====================================================
echo   Installation terminee avec succes !
echo  =====================================================
echo.
echo  Demarrage de JARVIS dans 3 secondes...
echo  (Assure-toi que ton microphone est branche)
echo.
timeout /t 3 /nobreak >nul

python jarvis.py

echo.
echo  JARVIS arrete.
pause
