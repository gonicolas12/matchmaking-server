# Serveur de Matchmaking pour Jeux de Plateau

Ce projet implémente un serveur de matchmaking pour des jeux de plateau au tour par tour comme le Tic-Tac-Toe. Il permet aux joueurs de s'inscrire, d'entrer dans une file d'attente et d'être mis en correspondance pour jouer les uns contre les autres.

## Fonctionnalités

- Serveur de matchmaking avec file d'attente
- Implémentation du jeu Tic-Tac-Toe
- Client graphique Python
- Base de données pour stocker les joueurs, matchs et tours
- Communication en temps réel via Socket.IO

## Prérequis

- Node.js 16+ et npm
- Python 3.8+
- SQLite3

## Installation

1. Cloner le dépôt
```bash
git clone https://github.com/gonicolas12/matchmaking-server.git
```
```bash
cd matchmaking-server
```

2. Installer les dépendances Node.js
```bash
npm install
```

3. Installer les dépendances Python
```bash
pip install python-socketio aiohttp
```

## Utilisation

1. Démarrer le serveur
```bash
npm run build
npm start
```

2. Démarrer le client
```bash
python python/game_client.py
```