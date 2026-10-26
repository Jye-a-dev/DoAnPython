# EduFlash AI Monorepo

He thong Flashcard AI kien truc Monorepo 3 tang dich vu doc lap.

## Cau truc thu muc

```text
my-monorepo/
├── client/                  # Frontend (NiceGUI / Web UI - Port 5000)
├── pipeline/                # AI Inference Microservice (Flan-T5, Whisper - Port 8000)
├── server/                  # Backend API Gateway & Database (Flask/FastAPI - Port 3000)
├── .env.example             # Bien moi truong mau cap root
├── .gitignore               # Bo quy tac chan cache, venv, secrets
└── README.md                # Tai lieu huong dan du an
```

## Khoi chay he thong

### 1. Khoi chay toan trinh bang Orchestrator
Khoi dong dong thoi ca 3 dich vu theo thu tu: Server (3000) -> Pipeline (8000) -> Client (5000) voi tinh nang graceful shutdown tu dong:

```bash
python server/scripts/run_e2e_stack.py
```

### 2. Khoi chay tung dich vu rieng biet

#### Backend Server (Port 3000)
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # Hoac .venv\Scripts\activate tren Windows
pip install -r requirements.txt
python app/main.py
```

#### AI Pipeline (Port 8000)
```bash
cd pipeline
python -m venv .venv
source .venv/bin/activate  # Hoac .venv\Scripts\activate tren Windows
pip install -r requirements.txt
python main.py
```

#### NiceGUI Client (Port 5000)
```bash
cd client
python -m venv .venv
source .venv/bin/activate  # Hoac .venv\Scripts\activate tren Windows
pip install -r requirements.txt
python main.py
```
