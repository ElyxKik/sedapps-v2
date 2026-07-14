#!/bin/bash
set -e

FLUTTER_PATH="/Users/elykik/Documents/seda.website/sala-ai-cloud/apps/mobile"
API_BASE_URL="${API_BASE_URL:-https://api.salaai.site}"

echo "🚀 Déploiement Flutter sur Firebase Hosting"
echo ""

# 1. Build Flutter web
echo "🔨 Build Flutter web..."
cd "$FLUTTER_PATH"
flutter build web \
  --no-wasm-dry-run \
  --dart-define=CORE_API_BASE_URL="$API_BASE_URL" \
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
echo "🔗 Application: https://sedapps.web.app"
echo "🔗 API serveur: $API_BASE_URL"
