# ✈️ Airspace Copilot: Real-Time Multi-Agent Flight Monitoring System

## 📖 Overview

The **Airspace Copilot** is an intelligent multi-agent AI system that monitors live flight traffic using the OpenSky Network API. It provides two specialized interfaces:

1. **Airspace Operations Copilot** - Monitors regional airspace, detects anomalies, and provides operational summaries
2. **Personal Flight Watchdog** - Tracks specific flights and answers traveler questions via natural language chat

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│              (HTML/CSS/JavaScript Frontend)                     │
│         • Operations View    • Traveler View                    │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP (Port 5000)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK API BRIDGE                             │
│                     (backend.py)                                │
│  • /api/ops/analyze    • /api/traveler/track                   │
│  • /api/traveler/ask   • /api/health                           │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             ▼                                ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│    AGENTIC LAYER             │   │    MCP SERVER                │
│    (agents.py - CrewAI)      │◄──┤    (mcp_server.py)           │
│                              │   │                              │
│  • Ops Analyst Agent         │   │  Tools:                      │
│  • Traveler Support Agent    │   │  • list_region_snapshot      │
│  • A2A Communication         │   │  • get_by_callsign           │
│                              │   │  • list_active_alerts        │
└──────────┬───────────────────┘   └──────────┬───────────────────┘
           │                                   │
           │ Groq LLM API                     │ Reads from
           │ (llama-3.3-70b)                  │
           │                                   ▼
           │                          ┌──────────────────────────┐
           │                          │   DATA STORAGE           │
           │                          │   (region1.json)         │
           │                          └──────────┬───────────────┘
           │                                     │
           │                                     │ Updated by
           ▼                                     ▼
    ┌──────────────────────────────────────────────────────────┐
    │                    n8n WORKFLOW                          │
    │         (Data Fetch & Preprocessing)                     │
    │                                                          │
    │  • Scheduled HTTP Request to OpenSky API                │
    │  • Data Filtering & Transformation                      │
    │  • JSON Storage                                         │
    │  • Webhook Endpoint for Manual Trigger                  │
    └──────────────────┬───────────────────────────────────────┘
                       │
                       ▼
            ┌───────────────────────┐
            │   OPENSKY NETWORK     │
            │   Public REST API     │
            └───────────────────────┘
```

## 🎯 Key Components

### 1. **n8n Workflow Orchestration**
- Fetches live flight data from OpenSky Network API
- Filters and preprocesses data (callsign, altitude, speed, etc.)
- Stores snapshots in `region1.json`
- Runs on schedule (every 60 seconds) or manual trigger
- Handles API rate limits and failures gracefully

### 2. **MCP (Model Context Protocol) Server**
- FastAPI-based REST server exposing flight data as structured tools
- Three main tools:
  - `flights.list_region_snapshot` - Returns all flights in a region
  - `flights.get_by_callsign` - Finds specific flight by ID
  - `alerts.list_active` - Returns flights with detected anomalies
- Implements rule-based anomaly detection logic
- Runs on port 8000

### 3. **Agentic Layer (CrewAI)**
Two specialized AI agents:
- **Ops Analyst Agent**: Analyzes regional airspace, generates summaries
- **Traveler Support Agent**: Tracks flights, answers questions
- **A2A Communication**: Traveler agent can call Ops agent for context
- Powered by Groq LLM API (llama-3.3-70b-versatile)
- Agents access data through MCP tools (not direct file access)

### 4. **Flask API Bridge**
- Lightweight REST API connecting frontend to agents
- Endpoints:
  - `POST /api/ops/analyze` - Operations analysis
  - `POST /api/traveler/track` - Track flight
  - `POST /api/traveler/ask` - Q&A chatbot
  - `GET /api/health` - Health check
- Runs on port 5000

### 5. **Frontend (HTML/CSS/JavaScript)**
- Single-page application with two modes
- Dark-themed, responsive design using Tailwind CSS
- Real-time communication with backend via Fetch API
- Loading states and error handling
- No external dependencies except CDN resources

## 📋 Prerequisites

- **Python 3.8+**
- **Docker** (for n8n)
- **Groq API Key** (free tier)
- **Internet connection** (for OpenSky API)

## 🚀 Installation & Setup

### Step 1: Clone/Download Project Structure

```
AGENTIC AI/A3/
├── n8n/
│   └── shared/
│       └── region1.json
├── mcp/
│   └── mcp_server.py
└── agents/
    ├── agents.py
    ├── backend.py
    ├── index.html
    ├── requirements.txt
    ├── .env
    └── simple_test.py
```

### Step 2: Install Python Dependencies

```bash
cd agents
pip install -r requirements.txt
```

**Dependencies:**
- `fastapi==0.115.0` - MCP server & backend API
- `uvicorn==0.32.0` - ASGI server
- `requests==2.32.3` - HTTP requests
- `groq==0.11.0` - Groq LLM API client
- `crewai==0.86.0` - Multi-agent framework
- `flask==3.0.0` - Backend API bridge
- `flask-cors==4.0.0` - CORS support
- `python-dotenv==1.0.1` - Environment variables

### Step 3: Configure Environment Variables

Create `.env` file in `agents/` directory:

```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

Get your free API key from: https://console.groq.com/

### Step 4: Setup n8n (Docker)

```bash
# Run n8n container with volume mount
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v "C:\Users\User\Downloads\AGENTIC AI\A3\n8n:/home/node/.n8n" \
  n8nio/n8n
```

Access n8n at: http://localhost:5678

### Step 5: Import n8n Workflow

1. Open http://localhost:5678
2. Click "Import from File"
3. Import `n8n_workflow_export.json`
4. Configure the workflow:
   - Set OpenSky API endpoint
   - Configure file write path to `shared/region1.json`
   - Set schedule interval (recommended: 60 seconds)
5. Activate the workflow

## ▶️ Running the System

The system requires **3 terminals** running simultaneously:

### Terminal 1: n8n (Data Ingestion)

```bash
# If not already running from setup
docker start n8n

# Or run fresh container
docker run -it --rm --name n8n -p 5678:5678 \
  -v "C:\Users\User\Downloads\AGENTIC AI\A3\n8n:/home/node/.n8n" \
  n8nio/n8n
```

**Expected Output:**
```
n8n ready on port 5678
Workflow "OpenSky Data Fetch" is active
```

**Verify:** Check that `region1.json` is being updated

---

### Terminal 2: MCP Server

```bash
cd mcp
python mcp_server.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Verify:** Visit http://localhost:8000/docs (FastAPI documentation)

---

### Terminal 3: Flask Backend

```bash
cd agents
python backend.py
```

**Expected Output:**
```
============================================================
🚀 AIRSPACE COPILOT - BACKEND API SERVER
============================================================

📡 API Endpoints Available:
   GET  /api/health           - Health check
   POST /api/ops/analyze      - Operations analysis
   POST /api/traveler/track   - Track flight
   POST /api/traveler/ask     - Ask question
   GET  /api/flights/list     - List all flights

🌐 Starting server on http://localhost:5000
============================================================
```

**Verify:** Visit http://localhost:5000/api/health

---

### Step 4: Open Frontend

Simply open `agents/index.html` in your web browser:
- Double-click the file, or
- Right-click → Open with → Chrome/Firefox/Edge

**Expected Result:**
- Green banner: "✅ Connected to AI Backend"
- Two tabs: Operations View and Traveler View

## 🧪 Testing the System

### Quick Test: Command Line

```bash
cd agents
python simple_test.py
```

This runs automated tests for:
- MCP server connection
- Operations mode analysis
- Traveler mode tracking
- Q&A with A2A communication

### Test 1: Operations Mode

1. Open `index.html` in browser
2. Click **"Operations View"** tab
3. Select **"region1"** from dropdown
4. Click **"Analyze Airspace"**

**Expected Result:**
- AI-generated summary of airspace status
- Statistics: Total flights, normal, anomalous
- Table showing all flights with anomaly flags
- Processing takes 3-5 seconds (Groq API call)

### Test 2: Traveler Mode - Flight Tracking

1. First run Operations analysis to see available flights
2. Copy a callsign from the table (e.g., `THY4KZ`)
3. Click **"Traveler View"** tab
4. Enter the callsign in the input field
5. Click **"Track Flight"**

**Expected Result:**
- Green status: "✅ Tracking: [callsign]"
- AI-generated flight summary
- Status indicator (normal/anomaly)
- Chat interface becomes active

### Test 3: Q&A Chatbot

After tracking a flight:

**Try these questions:**
- "Where is my flight now?"
- "What is my current altitude?"
- "Is my flight climbing or descending?"
- "Are there any other flights nearby that are having issues?" *(triggers A2A)*

**Expected Result:**
- Natural language answers based on real data
- 2-4 second response time
- Last question shows A2A communication (Traveler → Ops agent)

## 🔍 Verification Checklist

✅ **n8n running**: Visit http://localhost:5678  
✅ **Data updating**: Check `region1.json` has recent timestamp  
✅ **MCP server**: Visit http://localhost:8000/docs  
✅ **Flask backend**: Visit http://localhost:5000/api/health  
✅ **Frontend**: Open `index.html`, see green connection banner  
✅ **Operations mode**: Click analyze, see AI summary  
✅ **Traveler mode**: Track flight, see summary  
✅ **Chat**: Ask question, get AI answer  

## 🐛 Troubleshooting

### Problem: "Backend Offline" (Red Banner)

**Cause:** Flask backend not running or wrong port

**Solution:**
```bash
# Check if running
curl http://localhost:5000/api/health

# Restart backend
cd agents
python backend.py
```

---

### Problem: "Flight not found"

**Cause:** Flight not in current dataset or wrong callsign format

**Solution:**
1. Run Operations analysis first
2. Copy exact callsign from the table
3. Try with ICAO24 code instead (e.g., `4baa1a`)
4. Check `region1.json` has data

---

### Problem: Empty region1.json or No Flights

**Cause:** n8n not running, OpenSky API rate limited

**Solution:**
1. Check n8n workflow is active
2. Check workflow execution history for errors
3. OpenSky API may be rate-limited (wait 10-15 seconds)
4. For demos, save a working `region1.json` backup

---

### Problem: "GROQ_API_KEY not found"

**Cause:** Environment variable not set

**Solution:**
```bash
# Check .env file exists in agents/ folder
# Format should be:
GROQ_API_KEY=gsk_your_key_here

# No spaces around =
# No quotes around key
```

---

### Problem: CORS Errors in Browser Console

**Cause:** `flask-cors` not installed

**Solution:**
```bash
pip install flask-cors
# Restart backend.py
```

---

### Problem: MCP Server 500 Errors

**Cause:** Invalid JSON structure in region1.json

**Solution:**
1. Check JSON is valid (use jsonlint.com)
2. Verify structure matches expected format
3. Check file permissions (read access)

---

### Problem: Slow AI Responses (>10 seconds)

**Cause:** Network latency to Groq API

**Solution:**
- Normal response time: 2-5 seconds
- Check internet connection
- Groq free tier may have rate limits
- Try again after a minute

## 📊 API Endpoints Reference

### MCP Server (Port 8000)

```bash
# List all flights in region
GET http://localhost:8000/mcp/flights/list_region_snapshot/region1

# Get specific flight
GET http://localhost:8000/mcp/flights/get_by_callsign/THY4KZ

# List active alerts
GET http://localhost:8000/mcp/alerts/list_active

# API Documentation
GET http://localhost:8000/docs
```

### Flask Backend (Port 5000)

```bash
# Health check
GET http://localhost:5000/api/health

# Operations analysis
POST http://localhost:5000/api/ops/analyze
Content-Type: application/json
{"region": "region1"}

# Track flight
POST http://localhost:5000/api/traveler/track
Content-Type: application/json
{"flight_id": "THY4KZ"}

# Ask question
POST http://localhost:5000/api/traveler/ask
Content-Type: application/json
{"flight_id": "THY4KZ", "question": "Where is my flight?"}
```

## 📁 File Descriptions

### Core Components

| File | Description | Location |
|------|-------------|----------|
| `mcp_server.py` | MCP server with 3 flight data tools | `mcp/` |
| `agents.py` | Two AI agents with A2A communication | `agents/` |
| `backend.py` | Flask API bridge for frontend | `agents/` |
| `index.html` | Web-based user interface | `agents/` |
| `region1.json` | Flight data snapshot storage | `n8n/shared/` |

### Supporting Files

| File | Description |
|------|-------------|
| `simple_test.py` | Automated test suite |
| `requirements.txt` | Python dependencies |
| `.env` | Groq API key configuration |
| `README.md` | This file |

### n8n Workflow Export

The n8n workflow JSON should contain:
- HTTP Request node (OpenSky API)
- Function node (data filtering)
- File Write node (region1.json)
- Webhook trigger (manual execution)
- Schedule trigger (every 60s)

## 🎯 System Features

### ✅ Implemented Requirements

- [x] n8n workflow for data fetching and preprocessing
- [x] MCP server with 3 required tools
- [x] Two AI agents (Ops Analyst + Traveler Support)
- [x] A2A communication between agents
- [x] Groq LLM integration for natural language
- [x] Operations view with anomaly detection
- [x] Traveler view with chatbot interface
- [x] Simple, clean UI (HTML/CSS/JS)
- [x] Graceful API failure handling
- [x] Real-time data processing

### 🎨 Anomaly Detection Rules

The system detects:
1. **Low speed at high altitude** (< 40 m/s at > 3000m)
2. **Rapid vertical change** (|vertical_rate| > 15 m/s)
3. **Stationary at low altitude** (< 5 m/s at < 300m)

### 🤖 Agent Capabilities

**Ops Analyst Agent:**
- Analyzes regional flight patterns
- Identifies anomalous flights
- Generates operational summaries
- Recommends actions

**Traveler Support Agent:**
- Tracks specific flights
- Answers natural language questions
- Explains flight status in plain terms
- Calls Ops Agent when needed (A2A)

## 🔒 Security Notes

- OpenSky API used anonymously (no credentials required)
- Groq API key stored in `.env` (git-ignored)
- No sensitive data stored
- CORS enabled for local development
- All data processed locally except LLM calls

## 📈 Performance

- **API Response Time**: 2-5 seconds (Groq LLM)
- **Data Refresh**: Every 60 seconds (n8n)
- **MCP Server**: <100ms (local)
- **Frontend**: Instant load (no build step)

## 🚧 Known Limitations

1. **OpenSky API Rate Limits**: Anonymous access limited to 10 calls/minute
2. **Single Region**: Currently monitors one region at a time
3. **No Historical Data**: Only current snapshot available
4. **Rule-Based Anomalies**: Simple threshold-based detection
5. **No Authentication**: System runs locally without user accounts

## 🔮 Future Improvements

1. **Multi-Region Monitoring**: Parallel monitoring of multiple airspaces
2. **Historical Analysis**: Trend detection over time
3. **Advanced ML Anomalies**: ML-based anomaly detection
4. **Real-Time Alerts**: Push notifications for critical events
5. **Map Visualization**: Interactive flight map display
6. **Database Integration**: PostgreSQL for data persistence
7. **User Authentication**: Multi-user support
8. **Mobile App**: React Native companion app

## 📚 References

- **OpenSky Network**: https://opensky-network.org/
- **Groq Documentation**: https://console.groq.com/docs
- **CrewAI Framework**: https://github.com/joaomdmoura/crewAI
- **n8n Documentation**: https://docs.n8n.io/
- **MCP Protocol**: https://modelcontextprotocol.io/

## 👥 Authors

- Student Name: khadija Haider
- Course: Agentic AI Assignment 3
- Institution: National University of Computer and Emerging Sciences
- Course Instructor: Mr. Usama Imtiaz

## 📄 License

This project is submitted as coursework and follows academic integrity guidelines.

---

## 🆘 Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Verify all 3 terminals are running
3. Test each component individually using `simple_test.py`
4. Check browser console for errors
5. Review terminal outputs for error messages

---

**Last Updated**: November 2024  
**Version**: 1.0.0  
**Status**: Production Ready ✅
