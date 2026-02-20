# Sentinel-Watch 🚨🛰️

Real-time satellite monitoring system for environmental change detection using Sentinel-2 and Landsat-8 data.

## Features

- **Real-time Satellite Processing**: Continuous ingestion of Sentinel-2 and Landsat-8 imagery
- **Change Detection**: Automated detection of:
  - 🪓 Deforestation (NDVI analysis)
  - 🌊 Floods (NDWI analysis)
  - 🔥 Fire activity (SWIR analysis)
- **AI-Powered Analysis**: Vision models (Anthropic/OpenAI) for semantic analysis
- **Live Dashboard**: React-based UI with WebSocket real-time updates
- **Multi-channel Alerts**: Slack, Email, and SMS notifications

---

## Prerequisites

### macOS / Linux

- **Python 3.10+**
- **Docker** & **Docker Compose**
- **Node.js 18+** (for frontend development)
- **Git**

### Windows (Best Practice: WSL)

Windows users should use **Windows Subsystem for Linux (WSL2)** for the best experience.

```
powershell
# Install WSL2 (run in PowerShell as Administrator)
wsl --install -d Ubuntu
```

After installation, all commands below should be run inside your WSL terminal.

---

## Quick Start (Docker Compose - Recommended)

The easiest way to run Sentinel-Watch:

```
bash
# 1. Clone and navigate to project
cd sentinel-watch

# 2. Create environment file with your API keys
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Access the dashboard
# Frontend: http://localhost:3000
# API:      http://localhost:8765
# WebSocket: ws://localhost:8766
```

---

## Development Setup (Manual)

If you want to run components individually for development:

### 1. Backend Setup

```
bash
# Navigate to project directory
cd sentinel-watch

# Create virtual environment (macOS/Linux/WSL)
python3 -m venv venv
source venv/bin/activate  # On Windows (WSL): source venv/Scripts/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Kafka Setup

```bash
# Option A: Docker (recommended)
docker run -d \
  --name kafka \
  -p 9092:9092 \
  -e KAFKA_BROKER_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  confluentinc/cp-kafka:7.5.0

# Option B: Using docker-compose (includes Zookeeper)
docker-compose -f docker/docker-compose.yml up -d kafka zookeeper
```

### 3. Frontend Setup

```
bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Start Backend Services

```
bash
# Start REST API
python -m backend.api.rest_server

# Start Pathway stream processor (in another terminal)
python pathway_engine.py
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```
bash
# ── Satellite Data ─────────────────────────────────────────────
USGS_USERNAME=your_usgs_username
USGS_PASSWORD=your_usgs_password

# ── Vision Model (choose one) ──────────────────────────────────
VISION_PROVIDER=anthropic  # or "openai"
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# ── Kafka ─────────────────────────────────────────────────────
KAFKA_BROKERS=localhost:9092

# ── Alerts (optional) ─────────────────────────────────────────
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ALERT_EMAIL_FROM=alerts@example.com
ALERT_EMAIL_PASSWORD=your_app_password
ALERT_EMAIL_TO=recipient@example.com
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1234567890
ALERT_SMS_TO=+1234567890
```

### Detection Thresholds (Optional)

```
bash
DEFORESTATION_THRESHOLD=-0.25  # NDVI below this = deforestation
FLOOD_THRESHOLD=0.25          # NDWI above this = flood
FIRE_SWIR_THRESHOLD=0.75      # SWIR above this = fire
MAX_CLOUD_COVER=30             # Skip imagery with >30% clouds
```

---

## Running the Full Stack

### Using Docker Compose (All-in-one)

```
bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Manual Startup

```
bash
# Terminal 1: Start Kafka
docker-compose -f docker/docker-compose.yml up -d kafka zookeeper

# Terminal 2: Start Backend API
source venv/bin/activate
python -m backend.api.rest_server

# Terminal 3: Start Pathway Engine
source venv/bin/activate
python pathway_engine.py

# Terminal 4: Start Frontend
cd frontend && npm run dev
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/events` | GET | List all detected events |
| `/api/events/{id}` | GET | Get event details |
| `/api/stats` | GET | Get statistics |
| `/api/regions` | GET | List monitored regions |
| `/api/pipeline/status` | GET | Pipeline status |

**WebSocket**: `ws://localhost:8766` for real-time event streaming

---

## Project Structure

```
sentinel-watch/
├── backend/
│   ├── api/              # REST API server
│   ├── alerts/           # Alert handlers (Slack, Email, SMS)
│   ├── connectors/       # Satellite data connectors
│   ├── detection/        # NDVI, NDWI, SWIR detectors
│   └── knowledge_graph/  # Graph database utilities
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   └── utils/        # Utility functions
│   └── package.json
├── config/
│   ├── settings.py       # Configuration
│   └── regions.json      # Monitored regions
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── tests/
├── pathway_engine.py     # Stream processing engine
└── requirements.txt      # Python dependencies
```

---

## Troubleshooting

### Kafka Connection Issues

```
bash
# Check if Kafka is running
docker ps | grep kafka

# View Kafka logs
docker logs kafka

# Wait for Kafka to be ready (may take 30s)
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8765  # macOS
ss -tulpn | grep 8765  # Linux

# Kill the process
kill -9 <PID>
```

### Permission Errors (Linux/WSL)

```
bash
# Fix Docker permissions
sudo usermod -aG docker $USER
# Then logout and login again
```

---

## License

MIT License
