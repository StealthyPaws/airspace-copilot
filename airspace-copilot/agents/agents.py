"""
Airspace Copilot - Agentic System using CrewAI
File: agents/agents.py
"""

from crewai import Agent, Task, Crew
import requests
import json
import os
from groq import Groq

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "KEY")
client = Groq(api_key=GROQ_API_KEY)

MCP_BASE_URL = "http://localhost:8000/mcp"

# ============================================
# Helper Functions for MCP Tool Calls
# ============================================

def call_mcp_list_region(region_name="region1"):
    """Fetches flight snapshot for a region from MCP server."""
    try:
        response = requests.get(f"{MCP_BASE_URL}/flights/list_region_snapshot/{region_name}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"MCP returned status {response.status_code}", "flights": []}
    except Exception as e:
        return {"error": str(e), "flights": []}

def call_mcp_get_flight(callsign):
    """Fetches specific flight data by callsign/ICAO24."""
    try:
        response = requests.get(f"{MCP_BASE_URL}/flights/get_by_callsign/{callsign}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Flight {callsign} not found"}
    except Exception as e:
        return {"error": str(e)}

def call_mcp_list_alerts():
    """Fetches all active alerts from MCP server."""
    try:
        response = requests.get(f"{MCP_BASE_URL}/alerts/list_active", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"alerts": []}
    except Exception as e:
        return {"error": str(e), "alerts": []}

# ============================================
# Custom LLM Function using Groq
# ============================================

def groq_llm_call(prompt, max_tokens=1500):
    """Makes a call to Groq API with the given prompt."""
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert aviation operations analyst. Provide clear, concise, and accurate analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=max_tokens
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error calling Groq API: {str(e)}"

# ============================================
# Agent 1: Ops Analyst Agent
# ============================================

class OpsAnalystAgent:
    """Agent responsible for monitoring regional airspace and detecting anomalies."""
    
    def __init__(self):
        self.name = "Ops Analyst Agent"
    
    def analyze_region(self, region_name="region1"):
        """Analyzes a region and provides operational summary."""
        print(f"\n[{self.name}] Analyzing region: {region_name}")
        
        # Call MCP to get flight data
        region_data = call_mcp_list_region(region_name)
        
        if "error" in region_data:
            return f"Error fetching region data: {region_data['error']}"
        
        flights = region_data.get("flights", [])
        timestamp = region_data.get("timestamp", "N/A")
        
        # Count anomalies
        anomalous_flights = [f for f in flights if f.get("anomaly_label")]
        
        # Prepare summary for LLM
        summary_prompt = f"""
You are analyzing airspace operations for {region_name}.

Data timestamp: {timestamp}
Total flights: {len(flights)}
Anomalous flights: {len(anomalous_flights)}

Flight details:
{json.dumps(flights[:10], indent=2)}

Anomalous flights:
{json.dumps(anomalous_flights, indent=2)}

Provide a concise operational summary including:
1. Overall airspace status
2. Critical anomalies requiring attention
3. Recommended actions

Keep the response under 200 words.
"""
        
        analysis = groq_llm_call(summary_prompt, max_tokens=500)
        
        return {
            "region": region_name,
            "timestamp": timestamp,
            "total_flights": len(flights),
            "anomalous_flights": len(anomalous_flights),
            "analysis": analysis,
            "raw_data": {
                "all_flights": flights,
                "alerts": anomalous_flights
            }
        }
    
    def get_alerts_summary(self):
        """Gets summary of all active alerts."""
        alerts_data = call_mcp_list_alerts()
        alerts = alerts_data.get("alerts", [])
        
        if not alerts:
            return "No active alerts at this time."
        
        prompt = f"""
You are reviewing active flight alerts:

{json.dumps(alerts, indent=2)}

Provide a brief summary of the most critical issues and any patterns you observe.
Keep response under 150 words.
"""
        return groq_llm_call(prompt, max_tokens=400)

# ============================================
# Agent 2: Traveler Support Agent
# ============================================

class TravelerSupportAgent:
    """Agent responsible for helping travelers track specific flights."""
    
    def __init__(self):
        self.name = "Traveler Support Agent"
        self.ops_agent = OpsAnalystAgent()  # A2A communication capability
    
    def track_flight(self, flight_id):
        """Tracks a specific flight and provides user-friendly summary."""
        print(f"\n[{self.name}] Tracking flight: {flight_id}")
        
        flight_data = call_mcp_get_flight(flight_id)
        
        if "error" in flight_data:
            return f"Sorry, I couldn't find flight {flight_id}. Please check the callsign or ICAO24 code."
        
        # Generate natural language summary
        prompt = f"""
You are helping a traveler track their flight.

Flight data:
{json.dumps(flight_data, indent=2)}

Provide a friendly, clear update including:
1. Current location (latitude/longitude in plain terms)
2. Altitude and speed
3. Flight status (climbing/descending/cruising)
4. Any concerns or anomalies

Use plain language suitable for a non-technical traveler.
Keep response under 150 words.
"""
        
        summary = groq_llm_call(prompt, max_tokens=400)
        
        return {
            "flight_id": flight_id,
            "summary": summary,
            "raw_data": flight_data
        }
    
    def answer_question(self, flight_id, question):
        """Answers specific questions about a flight."""
        print(f"\n[{self.name}] Answering question about {flight_id}: {question}")
        
        flight_data = call_mcp_get_flight(flight_id)
        
        if "error" in flight_data:
            return f"I couldn't find flight {flight_id} to answer your question."
        
        # Check if question involves nearby flights - A2A communication
        if any(keyword in question.lower() for keyword in ["other flights", "nearby", "around", "near"]):
            print(f"[{self.name}] Requesting regional context from Ops Analyst Agent...")
            ops_summary = self.ops_agent.get_alerts_summary()
            context = f"\n\nRegional context from Ops Analyst:\n{ops_summary}"
        else:
            context = ""
        
        prompt = f"""
A traveler tracking flight {flight_id} asks: "{question}"

Flight data:
{json.dumps(flight_data, indent=2)}
{context}

Provide a clear, helpful answer based on the available data.
Keep response under 150 words.
"""
        
        answer = groq_llm_call(prompt, max_tokens=400)
        return answer
    
    def check_flight_issues(self, flight_id):
        """Checks if there are any issues with the flight."""
        flight_data = call_mcp_get_flight(flight_id)
        
        if "error" in flight_data:
            return "Flight not found."
        
        anomaly = flight_data.get("anomaly_label")
        
        if anomaly:
            return f"⚠️ Alert: {anomaly}. Please monitor your flight status closely."
        else:
            return "✓ Your flight appears to be operating normally."

# ============================================
# Main Orchestration Functions
# ============================================

def run_ops_mode(region_name="region1"):
    """Runs operations mode analysis."""
    ops_agent = OpsAnalystAgent()
    result = ops_agent.analyze_region(region_name)
    return result

def run_traveler_mode(flight_id, question=None):
    """Runs traveler mode for flight tracking."""
    traveler_agent = TravelerSupportAgent()
    
    # Get basic flight info
    flight_info = traveler_agent.track_flight(flight_id)
    
    # If there's a specific question, answer it
    if question:
        answer = traveler_agent.answer_question(flight_id, question)
        flight_info["qa_response"] = answer
    
    # Check for issues
    issues = traveler_agent.check_flight_issues(flight_id)
    flight_info["issues"] = issues
    
    return flight_info

# ============================================
# Test Functions
# ============================================

def test_system():
    """Tests the complete system."""
    print("="*60)
    print("TESTING AIRSPACE COPILOT SYSTEM")
    print("="*60)
    
    # Test 1: Ops Mode
    print("\n[TEST 1] Operations Mode - Region Analysis")
    print("-"*60)
    ops_result = run_ops_mode("region1")
    print(f"Region: {ops_result['region']}")
    print(f"Total Flights: {ops_result['total_flights']}")
    print(f"Anomalous Flights: {ops_result['anomalous_flights']}")
    print(f"\nAnalysis:\n{ops_result['analysis']}")
    
    # Test 2: Traveler Mode
    print("\n\n[TEST 2] Traveler Mode - Flight Tracking")
    print("-"*60)
    
    # Get first available flight for testing
    if ops_result['total_flights'] > 0:
        test_flight = ops_result['raw_data']['all_flights'][0]
        test_callsign = test_flight.get('callsign') or test_flight.get('icao24')
        
        if test_callsign:
            traveler_result = run_traveler_mode(test_callsign.strip())
            print(f"Flight ID: {traveler_result['flight_id']}")
            print(f"\nSummary:\n{traveler_result['summary']}")
            print(f"\n{traveler_result['issues']}")
    else:
        print("No flights available for testing traveler mode.")
    
    # Test 3: Q&A with A2A communication
    print("\n\n[TEST 3] Traveler Q&A with A2A Communication")
    print("-"*60)
    if ops_result['total_flights'] > 0:
        test_flight = ops_result['raw_data']['all_flights'][0]
        test_callsign = test_flight.get('callsign') or test_flight.get('icao24')
        
        if test_callsign:
            question = "Are there any other flights nearby that are having issues?"
            answer = run_traveler_mode(test_callsign.strip(), question)
            print(f"Question: {question}")
            print(f"\nAnswer:\n{answer.get('qa_response', 'N/A')}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    # Set your Groq API key here or in environment variable
    if GROQ_API_KEY == "KEY":
        print("WARNING: Please set your GROQ_API_KEY")
        print("You can set it as an environment variable or edit the code directly.")
    else:
        test_system()