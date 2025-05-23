# 🎮 Serveur de Matchmaking - Chess & Tic-Tac-Toe

Ce projet implémente un serveur de matchmaking complet pour des jeux de plateau, avec support pour les **échecs** et le **tic-tac-toe**. Il permet aux joueurs de s'inscrire, d'entrer dans une file d'attente et d'être mis en correspondance pour jouer les uns contre les autres en temps réel.

## ✨ Fonctionnalités

### 🏆 Jeux Disponibles

#### ♟️ **Échecs (Chess)**
- **Règles complètes** : Toutes les règles standard des échecs
- **Mouvements spéciaux** : Roque, prise en passant, promotion du pion
- **Détection intelligente** : Échec, échec et mat, pat
- **Interface graphique** : Belle interface avec pièces Unicode
- **Validation des coups** : Validation complète des mouvements
- **Indication visuelle** : Surlignage des coups légaux et du dernier mouvement

#### ⭕ **Tic-Tac-Toe**
- **Jeu classique** : Grille 3x3 traditionnelle
- **Interface simple** : GUI intuitive et réactive
- **Matchs rapides** : Parfait pour des parties courtes

### 🌐 Architecture Serveur
- **Matchmaking automatique** : Files d'attente séparées par type de jeu
- **Communication temps réel** : Via Socket.IO
- **Base de données** : Stockage SQLite pour les joueurs, matchs et tours
- **API REST** : Endpoints pour les statistiques et informations
- **Gestion robuste** : Déconnexions, abandons, erreurs

## 🚀 Installation

### Prérequis
- **Node.js** 16+ et npm
- **Python** 3.8+
- **SQLite3**

### 1. Cloner le dépôt
```bash
git clone https://github.com/gonicolas12/matchmaking-server.git
cd matchmaking-server
```

### 2. Installer les dépendances Node.js
```bash
npm install
```

### 3. Installer les dépendances Python
```bash
pip install python-socketio aiohttp tkinter
```

## 🎯 Utilisation

### Démarrer le serveur
```bash
npm run build

npm start
```

Le serveur sera accessible à `http://localhost:3000`

### Lancer les clients

#### Option 1: Lanceur de jeu (Recommandé)
```bash
python game_launcher.py
```
Interface graphique pour choisir entre Chess et Tic-Tac-Toe.

#### Option 2: Clients directs
```bash
python chess_client.py

python game_client.py
```

## 🎮 Guide de Jeu

### Échecs

#### Interface
- **Plateau 8x8** avec coordonnées (a-h, 1-8)
- **Pièces Unicode** : ♔♕♖♗♘♙ (ou ASCII si souhaité)
- **Couleurs** : Cases claires/sombres, surlignage des coups
- **Panneau d'informations** : Statut, pièces capturées, contrôles

#### Gameplay
1. **Sélection** : Cliquez sur une de vos pièces
2. **Mouvement** : Cliquez sur une case de destination valide
3. **Promotion** : Interface popup pour choisir la pièce de promotion
4. **Abandon** : Bouton "Resign" pour abandonner

#### Règles Implémentées
- ✅ Tous les mouvements de pièces standards
- ✅ Roque (petit et grand)
- ✅ Prise en passant
- ✅ Promotion du pion (Dame, Tour, Fou, Cavalier)
- ✅ Détection d'échec et échec et mat
- ✅ Détection de pat (stalemate)
- ✅ Validation complète des coups

### Tic-Tac-Toe
- **Grille 3x3** simple et claire
- **Tour par tour** : X commence toujours
- **Victoire** : 3 en ligne (horizontal, vertical, diagonal)
- **Match nul** : Grille pleine sans vainqueur

## 📁 Structure du Projet

```
matchmaking-server/
├── src/
│   ├── server.ts              # Serveur principal
│   ├── services/
│   │   ├── database.ts        # Service base de données
│   │   └── gamelogic.ts       # Service logique de jeu
├── python/
│   ├── chess_client.py        # Client d'échecs
│   ├── chess_logic.py         # Logique d'échecs
│   ├── game_client.py         # Client tic-tac-toe
│   └── game_logic.py          # Logique tic-tac-toe
├── game_launcher.py           # Lanceur de jeu
├── database/
│   └── database.sqlite        # Base de données (auto-créée)
├── package.json
├── tsconfig.json
└── README.md
```

## 🔧 Configuration

### Variables d'environnement
```bash
PORT=3000
NODE_ENV=development
```

### Personnalisation
- **Server URL** : Modifiable dans le lanceur ou directement dans les clients
- **Style de pièces** : Toggle Unicode/ASCII dans le client d'échecs
- **Timeouts** : Configurables dans le code serveur

## 📊 API Endpoints

### GET `/`
Page d'accueil avec statut du serveur

### GET `/api/games`
Liste des jeux disponibles

### GET `/api/stats`
Statistiques en temps réel :
```json
{
  "chess_queue": 2,
  "tictactoe_queue": 1,
  "active_matches": 5,
  "total_players": 12
}
```

### GET `/api/players/:id`
Informations sur un joueur spécifique

## 🎯 Événements Socket.IO

### Client → Serveur
- `register` : Inscription d'un joueur
- `join_queue` : Rejoindre une file d'attente
- `make_move` : Effectuer un mouvement
- `resign_match` : Abandonner une partie

### Serveur → Client
- `registered` : Confirmation d'inscription
- `queue_joined` : Confirmation d'entrée en file
- `match_found` : Match trouvé
- `game_update` : Mise à jour de l'état du jeu
- `opponent_disconnected` : Déconnexion de l'adversaire
- `error` : Messages d'erreur

## 🏗️ Architecture Technique

### Backend (Node.js + TypeScript)
- **Express.js** : Serveur web et API REST
- **Socket.IO** : Communication temps réel
- **SQLite** : Base de données embarquée
- **Python Shell** : Exécution de la logique de jeu en Python

### Frontend (Python + Tkinter)
- **Interface graphique** : Tkinter pour les clients
- **Async/await** : Communication asynchrone avec le serveur
- **Threading** : Gestion de l'event loop asyncio

### Base de Données
- **Tables** : players, matches, turns, queue_entries, games
- **Relations** : Clés étrangères pour maintenir l'intégrité
- **JSON Storage** : États de jeu stockés en JSON

## 🎓 Fonctionnalités Bonus

### Implémentées ✅
- **Multi-jeux** : Support Chess + Tic-Tac-Toe
- **Interface avancée** : GUI riche avec animations visuelles
- **Files séparées** : Matchmaking par type de jeu
- **Statistiques** : API de monitoring en temps réel
- **Abandon** : Possibilité de démissionner
- **Reconnexion** : Gestion robuste des déconnexions

### Possibles Extensions 🚀
- **IA Locale** : Jouer contre l'ordinateur
- **Tournois** : Système de tournois automatisés
- **Replay** : Revoir les parties jouées
- **Ratings** : Système de classement ELO
- **Chat** : Communication entre joueurs
- **Autres jeux** : Dames, Puissance 4, etc.

## 🐛 Dépannage

### Problèmes Courants

#### "Module not found"
```bash
npm install
pip install python-socketio aiohttp tkinter
```

#### "Connection refused"
```bash
npm start
```

#### "Python script not found"
```bash
ls python/
```

### Logs
- **Serveur** : Logs dans la console Node.js
- **Client** : Messages dans la console Python

## 📝 Développement

### Compilation TypeScript
```bash
npm run build
npm run dev
```

### Tests
```bash
npm test
```

### Structure des commits
- `feat:` nouvelles fonctionnalités
- `fix:` corrections de bugs  
- `docs:` documentation
- `style:` formatage
- `refactor:` refactoring
- `test:` tests

## 👥 Contribution

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🙏 Remerciements

- **Ynov Campus** pour le sujet du projet
- **Communauté Open Source** pour les outils utilisés
- **Chess.com** pour l'inspiration de l'interface d'échecs

---

**Projet réalisé dans le cadre du Bachelor 2 Informatique - Ynov Campus Bordeaux**

*Développement Logiciel et Base de données - Projet de Matchmaking*