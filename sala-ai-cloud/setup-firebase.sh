#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
FLUTTER_PATH="/Users/elykik/Documents/seda.website/sala-ai-cloud/apps/mobile"

echo "🔥 Configuration Firebase pour Flutter"
echo ""

# 1. Vérifier que Firebase CLI est installé
echo "🔍 Vérification de Firebase CLI..."
if ! command -v firebase &> /dev/null; then
  echo "❌ Firebase CLI n'est pas installé"
  echo "📦 Installation: npm install -g firebase-tools"
  exit 1
fi

echo "✅ Firebase CLI trouvé"
echo ""

# 2. Vérifier que Flutter est installé
echo "🔍 Vérification de Flutter..."
if ! command -v flutter &> /dev/null; then
  echo "❌ Flutter n'est pas installé"
  exit 1
fi

echo "✅ Flutter trouvé"
echo ""

# 3. Se connecter à Firebase
echo "🔐 Connexion à Firebase..."
firebase login

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Prochaines étapes:"
echo ""
echo "1. Créer un projet Firebase:"
echo "   - Aller sur https://console.firebase.google.com"
echo "   - Créer un nouveau projet nommé 'sala-ai-cloud'"
echo "   - Activer Firebase Hosting"
echo ""
echo "2. Mettre à jour .firebaserc avec votre project ID:"
echo "   nano $FLUTTER_PATH/.firebaserc"
echo ""
echo "3. Déployer l'application:"
echo "   chmod +x /Users/elykik/Documents/seda.website/sala-ai-cloud/deploy-firebase.sh"
echo "   /Users/elykik/Documents/seda.website/sala-ai-cloud/deploy-firebase.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
