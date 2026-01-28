# 🍓 Dashboard Monitoring Raspberry Pi

Dashboard de monitoring temps réel pour Raspberry Pi avec métriques système, historique, et alertes.

![Dashboard Preview](docs/preview.png)

## ✨ Fonctionnalités

- 📊 **Métriques temps réel** : CPU, RAM, Disque, Température
- 🔌 **WebSocket** : Mise à jour automatique toutes les 2 secondes
- 📈 **Historique** : Données stockées en SQLite (24h)
- ⚠️ **Alertes** : Seuils configurables pour CPU/RAM/Temp
- 📱 **Responsive** : Interface adaptée mobile/desktop
- 🐳 **Docker Ready** : Déploiement simple avec Docker Compose

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (HTML/JS)                   │
│           Chart.js │ WebSocket │ Responsive              │
├─────────────────────────────────────────────────────────┤
│                        Nginx                             │
│           Static Files │ Reverse Proxy │ WebSocket       │
├─────────────────────────────────────────────────────────┤
│                   FastAPI Backend                        │
│           REST API │ WebSocket │ psutil │ SQLite         │
├─────────────────────────────────────────────────────────┤
│                   Raspberry Pi                           │
│           CPU │ RAM │ Disk │ Temperature                 │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Déploiement sur Raspberry Pi

### Prérequis

- Raspberry Pi 4 avec Raspberry Pi OS
- Docker et Docker Compose installés

### Installation Docker (si nécessaire)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Déconnexion/Reconnexion nécessaire
```

### Déploiement

1. **Cloner le projet**
```bash
git clone https://github.com/chakh98-jpg/Dashboard_Pi.git
cd Dashboard_Pi
```

2. **Configurer l'environnement (optionnel)**
```bash
cp .env.example .env
nano .env  # Modifier les seuils d'alerte si besoin
```

3. **Lancer avec Docker Compose**
```bash
docker compose up -d --build
```

4. **Accéder au dashboard**
```
http://IP_DU_PI:80
```

## 📡 API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/metrics` | Métriques actuelles |
| GET | `/api/metrics/history?hours=24` | Historique |
| GET | `/api/metrics/stats?hours=1` | Statistiques |
| GET | `/api/system` | Info système |
| GET | `/api/health` | Health check |
| WS | `/ws` | WebSocket temps réel |

## ⚙️ Configuration

Variables d'environnement dans `.env` :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `COLLECTION_INTERVAL` | 2 | Intervalle de collecte (secondes) |
| `HISTORY_RETENTION_HOURS` | 24 | Durée de rétention des données |
| `CPU_ALERT_THRESHOLD` | 80.0 | Seuil d'alerte CPU (%) |
| `RAM_ALERT_THRESHOLD` | 80.0 | Seuil d'alerte RAM (%) |
| `TEMP_ALERT_THRESHOLD` | 70.0 | Seuil d'alerte température (°C) |

## 🔧 Commandes utiles

```bash
# Voir les logs
docker compose logs -f

# Redémarrer
docker compose restart

# Arrêter
docker compose down

# Mettre à jour
git pull
docker compose up -d --build
```

## 📁 Structure du projet

```
Dashboard_Pi/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # SQLite setup
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── collector.py     # Metrics collector
│   │   ├── websocket.py     # WebSocket manager
│   │   └── routes/          # API routes
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/dashboard.js
├── docker-compose.yml
├── nginx.conf
├── .env.example
└── README.md
```

## 📄 License

MIT License

---

Made with ❤️ for Raspberry Pi
