#!/bin/bash

# Script pour exécuter le scraper avec l'environnement virtuel
echo "🚀 Démarrage du scraper de bières V&B..."

# Se déplacer dans le répertoire du script
cd "$(dirname "$0")"

# Activer l'environnement virtuel et exécuter le scraper
source .venv/bin/activate && python scraper.py

echo "✅ Scraping terminé !"
