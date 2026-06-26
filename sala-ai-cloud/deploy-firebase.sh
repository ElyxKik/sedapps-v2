#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
FLUTTER_PATH="/Users/elykik/Documents/seda.website/sala-ai-cloud/apps/mobile"

echo "🚀 Déploiement Flutter sur Firebase Hosting"
echo ""

# 1. Build Flutter web
echo "🔨 Build Flutter web..."
cd "$FLUTTER_PATH"
flutter build web \
  --dart-define=CORE_API_BASE_URL=https://api.winandbet.online \
  --dart-define=MOCK_DATA=false \
  --release

# 2. Initialiser Firebase (si pas déjà fait)
echo "🔥 Initialisation Firebase..."
if [ ! -f "firebase.json" ]; then
  firebase init hosting
fi

# 3. Déployer sur Firebase
echo "📤 Déploiement sur Firebase..."
firebase deploy --only hosting

echo ""
echo "✨ Déploiement terminé!"
echo ""
echo "📍 Votre app est disponible à l'URL Firebase"
echo "🔗 API serveur: http://$SERVER_IP:8000"
