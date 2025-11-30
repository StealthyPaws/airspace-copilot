from fastapi import FastAPI, HTTPException
import json
import os
from typing import Dict, Any, List

app = FastAPI(title="Airspace Copilot MCP Server")
# !!! CRITICAL: Set to region1.json or ensure region2.json exists !!!
DATA_PATH = r"C:\Users\User\Downloads\AGENTIC AI\A3\n8n\shared\region1.json" # Reverted to region1 as it's the file you debugged

# --- Anomaly Logic (Revised for robustness) ---
# mcp_server.py (UPDATED get_anomaly_label for maximum safety against None)
def get_anomaly_label(flight: dict) -> str | None:
    """
    Applies hard-coded rules to detect anomalies, ensuring numerical values.
    """
    
    # Helper function to safely convert any value to float, defaulting to 0.0 if None or conversion fails.
    def safe_float(value):
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            # Fallback for unexpected string/type data that might appear
            return 0.0

    # 1. Safely extract and combine altitude fields
    geo_alt = flight.get('geo_altitude')
    baro_alt = flight.get('baro_altitude')
    
    # alt_m will be the safe_float of the first valid altitude, or 0.0 if all are None/missing.
    alt_m = safe_float(geo_alt if geo_alt is not None else baro_alt)
    
    # 2. Safely extract velocity and vertical rate
    vel_mps = safe_float(flight.get('velocity'))
    vrate_mps = safe_float(flight.get('vertical_rate'))
    
    # --- Anomaly Rules ---
    
    # Rule 1: Low speed at high altitude
    if alt_m > 3000 and vel_mps < 40:
        return "Anomaly: Low speed at high altitude"
    
    # Rule 2: Sudden large vertical rate
    if abs(vrate_mps) > 15:
        return "Anomaly: Rapid vertical change"
    
    # Rule 3: Near-stationary at low altitude
    if alt_m < 300 and vel_mps < 5: 
        return "Anomaly: Stationary at low altitude"

    return None

# --- Data Loading Function (FIXED to handle list wrapper) ---
def load_data() -> Dict[str, Any]:
    """Helper to safely load and UNWRAP the JSON snapshot."""
    
    if not os.path.exists(DATA_PATH):
        print(f"Warning: Data file not found at {DATA_PATH}")
        return {"snapshot": [], "timestamp": 0} 
    
    try:
        with open(DATA_PATH, 'r') as f:
            data = json.load(f)
            
            # 🚨 FIX: UNWRAP THE DATA FROM THE ROOT LIST 🚨
            # If the root is a list and contains one item (the dictionary), unwrap it.
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            
            # Final CRITICAL CHECK
            if not isinstance(data, dict) or "snapshot" not in data or not isinstance(data["snapshot"], list):
                 print(f"Error: JSON structure is invalid. Expected root dict with 'snapshot' key.")
                 return {"snapshot": [], "timestamp": 0}
            
            # The timestamp might be missing if n8n didn't include it. Add a safe default.
            if "timestamp" not in data:
                 data["timestamp"] = 0
            
            return data
            
    except Exception as e:
        print(f"CRITICAL ERROR loading data from {DATA_PATH}: {e}")
        return {"snapshot": [], "timestamp": 0}

# --- MCP Tool 1: flights.list_region_snapshot ---
@app.get("/mcp/flights/list_region_snapshot/{region_name}")
def list_region_snapshot(region_name: str):
    """Returns the raw flight list for a region."""
    data = load_data()
    
    # The anomaly label must be calculated on the loaded data BEFORE returning.
    for flight in data["snapshot"]:
        flight["anomaly_label"] = get_anomaly_label(flight)
        
    return {
        "timestamp": data.get("timestamp"),
        "flights": data["snapshot"]
    }

# --- MCP Tool 2: flights.get_by_callsign ---
@app.get("/mcp/flights/get_by_callsign/{callsign}")
def get_flight_by_callsign(callsign: str):
    """Finds the latest record for a given flight identifier."""
    flights = load_data()["snapshot"]
    
    for flight in flights:
        current_callsign = (flight.get('callsign') or "").strip()
        current_icao24 = flight.get('icao24')
        
        if (current_callsign.upper() == callsign.upper()) or (current_icao24 and current_icao24.upper() == callsign.upper()):
            flight["anomaly_label"] = get_anomaly_label(flight)
            return flight

    raise HTTPException(status_code=404, detail=f"Flight {callsign} not found in latest snapshot.")

# --- MCP Tool 3: alerts.list_active ---
@app.get("/mcp/alerts/list_active")
def list_active_alerts():
    """Returns a list of all flights currently flagged as anomalous."""
    flights = load_data()["snapshot"]
    active_alerts = []
    
    for flight in flights:
        anomaly = get_anomaly_label(flight)
        if anomaly:
            active_alerts.append({
                "callsign": (flight.get('callsign') or flight.get('icao24')),
                "icao24": flight.get('icao24'),
                "latitude": flight.get('latitude'),
                "longitude": flight.get('longitude'),
                "anomaly_label": anomaly,
                "details": f"Alt: {flight.get('geo_altitude', 'N/A')}m, Speed: {flight.get('velocity', 'N/A')}m/s, VRate: {flight.get('vertical_rate', 'N/A')}m/s"
            })
            
    return {"alerts": active_alerts}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)