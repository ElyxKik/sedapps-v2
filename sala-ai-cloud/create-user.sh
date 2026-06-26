#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"
REMOTE_PATH="/opt/sedapps"
EMAIL="kikuniely@gmail.com"
PASSWORD="MyxeezyLife*"  # À changer après la création

echo "👤 Création d'un nouvel utilisateur"
echo "📧 Email: $EMAIL"
echo ""

# 1. Créer l'utilisateur via l'API
echo "📤 Envoi de la requête d'inscription..."

RESPONSE=$(curl -s -X POST "http://193.168.175.108:8000/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\",
    \"full_name\": \"Kikuni Ely\"
  }")

echo "Réponse: $RESPONSE"
echo ""

# 2. Vérifier la réponse
if echo "$RESPONSE" | grep -q "user_id\|id"; then
  echo "✅ Utilisateur créé avec succès!"
  echo ""
  echo "📋 Identifiants:"
  echo "  Email: $EMAIL"
  echo "  Mot de passe: $PASSWORD"
  echo ""
  echo "⚠️  IMPORTANT: Changer le mot de passe après la première connexion!"
else
  echo "❌ Erreur lors de la création"
  echo "Réponse complète: $RESPONSE"
  exit 1
fi

echo ""
echo "🌐 Accès à l'application:"
echo "  URL: https://sedapps.web.app"
echo "  Email: $EMAIL"
echo "  Mot de passe: $PASSWORD"
