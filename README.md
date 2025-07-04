# 🤖 Vocca Voice AI Chatbot — MongoDB & Docker

Ce projet implémente un assistant vocal interactif basé sur backend [Pipecat](https://github.com/pipecat-ai/pipecat/exemples/simple-chatbot) et frontend (https://github.com/daily-demos/daily-bots-web-demo), avec :

* 🤖 Un chatbot vocal animé utilisant **Cartesia** pour LLM & TTS
* 🎙️ Transcription audio en temps réel avec **Daily**
* 🧠 Une base de données MongoDB pour la gestion des rendez-vous
* 🧱 Une architecture en microservices (frontend & backend)
* 🚀 Déploiement backend avec Docker

---

## 📁 Structure du projet

```
Voccatestsalma/
│
├── client/                    # Frontend Next.js + React
│
├── simple-server/            # Backend Pipecat
│   ├── assets/               # Images de l'avatar animé (robot01.png à robot025.png)
│   ├── bot-openai.py         # Implémentation du bot (OpenAI ou Cartesia)
│   ├── confirm_logic.py      # Logique métier (prise de rendez-vous)
│   ├── event_handlers.py     # Gestion des événements (Daily, RTVI)
│   ├── mongo_loader.py       # Connexion MongoDB
│   ├── server.py             # Point d'entrée principal (FastAPI)
│   ├── runner.py             # Initialisation du pipeline Pipecat
│   ├── sprite_utils.py       # Gestion des animations
│   ├── setup_services.py     # Initialisation des services LLM, TTS
│   ├── requirements.txt      # Dépendances Python
│   ├── init_bookings.json    # Données d'initialisation pour les rendez-vous
│   ├── init_departments.json # Données d'initialisation pour les départements
│   ├── env.example           # Exemple de fichier d'environnement
│   └── Dockerfile            # Docker backend
│
└── README.md
```

---

## 🎨 Structure du Frontend (Client)

Le frontend est basé sur **Next.js 14** avec les composants suivants :

```
client/
├── app/
│   ├── layout.tsx           # Layout principal de l'application
│   ├── page.tsx             # Page d'accueil
│   └── global.css           # Styles globaux
├── components/
│   ├── App.tsx              # Composant principal
│   ├── context.tsx          # Context React pour l'état global
│   ├── Header/              # En-tête avec timer d'expiration
│   ├── Session/             # Gestion de session avec agent et stats
│   ├── Setup/               # Configuration initiale (devices, prompts)
│   └── ui/                  # Composants UI réutilisables (buttons, inputs, etc.)
├── types/
│   └── stats_aggregator.d.ts # Types TypeScript pour les statistiques
├── utils/
│   ├── stats_aggregator.ts  # Utilitaires pour les statistiques
│   └── tailwind.ts          # Utilitaires Tailwind CSS
├── public/
│   └── color-wash-bg.png    # Assets statiques
├── package.json             # Dépendances Next.js + React
├── next.config.mjs          # Configuration Next.js
├── tailwind.config.ts       # Configuration Tailwind CSS
├── rtvi.config.ts           # Configuration RTVI (Real-Time Voice Interface)
└── env.example              # Exemple de variables d'environnement
```

### Configuration du client

Créer un fichier `.env.local` dans `client/` :

```bash
cd client
cp env.example .env.local
```

---

## 🧪 Fonctionnalités

* 🎤 Prise de parole et transcription via [Daily.co](https://www.daily.co/)
* 💬 Réponse textuelle via **Cartesia API** ou OpenAI (GPT)
* 🔈 Conversion vocale avec **Cartesia** ou autres TTS intégrés
* 🗂️ Sauvegarde des rendez-vous dans MongoDB
* 📆 Gestion dynamique des disponibilités selon `operating_hours`
* 🎨 Interface web Next.js avec composants React modernes
* 🚀 Backend FastAPI avec Pipecat pour le traitement en temps réel
* 🐳 Déploiement containerisé avec Docker

---

## 🧬 Base de données MongoDB

La base `vocca-ai` contient 2 collections principales :

### 🏥 `departments`

```json
{
  "name": "Cardiology",
  "operating_hours": [
    { "day_of_week": "Monday", "start_time": "09:00", "end_time": "17:00" },
    { "day_of_week": "Wednesday", "start_time": "09:00", "end_time": "17:00" }
  ]
}
```

### 📅 `bookings`

```json
{
  "department_id": ObjectId("..."),
  "user_id": 101,
  "booking_time": "2025-07-04T10:30:00Z",
  "status": "confirmed"
}
```

---

## ⚙️ Pré-requis

* Python 3.10+
* Node.js 18+
* Docker
* MongoDB Atlas (ou local)
* API keys :

  * `OPENAI_API_KEY` ou `CARTESIA_API_KEY`
  * `CARTESIA_VOICE_ID` (si Cartesia est utilisé)
  * `DAILY_API_KEY`

---

## 🚀 Lancer le projet

### 1. Cloner le repo et se placer dans le répertoire

```bash
git clone https://github.com/salmaelyagoubi/vocca-voice-ai-chatbot.git
cd vocca-voice-ai-chatbot
```

### 2. Configurer l'environnement backend

Créer un fichier `.env` dans `simple-server/` à partir de `env.example` :

```bash
cd simple-server
cp env.example .env
```

> Exemple de fichier `.env` :

```
DAILY_SAMPLE_ROOM_URL=https://your-daily-room-url
DAILY_API_KEY=xxx
OPENAI_API_KEY=xxx
CARTESIA_API_KEY=xxx
CARTESIA_VOICE_ID=xxx
BOT_IMPLEMENTATION=cartesia
MONGO_URI=mongodb+srv://user:password@host.mongodb.net/
MONGO_DB=vocca-ai
```

### 3. Option A : Lancer avec Docker (recommandé)

```bash
# Depuis le répertoire simple-server/
docker build -t vocca .
docker run --env-file .env -p 7860:7860 vocca
```

### 3. Option B : Lancer en local

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Lancer le serveur
python server.py
```

### 4. Démarrer le frontend

```bash
cd ../client
npm install
npm run dev
```

Le client sera disponible sur `http://localhost:3000` (Next.js).

---

## 🧠 Crédits

* [Pipecat AI](https://github.com/pipecat-ai/pipecat)
* [Daily API](https://docs.daily.co/)
* [Cartesia AI](https://cartesia.ai)
* [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
