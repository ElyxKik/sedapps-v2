#!/bin/bash
set -e

SERVER_IP="193.168.175.108"
SERVER_USER="root"

echo "🐳 Installation de Docker sur $SERVER_IP..."

ssh $SERVER_USER@$SERVER_IP << 'REMOTE_SCRIPT'
set -e

echo "📦 Mise à jour des paquets..."
apt-get update
apt-get upgrade -y

echo "🔧 Installation des dépendances..."
apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

echo "🔑 Ajout de la clé GPG Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "📝 Ajout du repository Docker..."
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "📦 Installation de Docker..."
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "✅ Démarrage de Docker..."
systemctl start docker
systemctl enable docker

echo "👤 Ajout de l'utilisateur au groupe docker..."
usermod -aG docker $USER || true

echo "🔍 Vérification de l'installation..."
docker --version
docker compose version

echo "✨ Docker installé avec succès!"
REMOTE_SCRIPT

echo ""
echo "✅ Installation terminée!"
echo ""
echo "⚠️  Note: Vous devrez peut-être vous reconnecter pour que les permissions de groupe prennent effet."
echo ""
echo "Prochaine étape: Lancer le déploiement avec:"
echo "  ./deploy.sh"
