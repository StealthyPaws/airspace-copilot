"""
Flask Backend - Connects HTML Frontend to Agents
File: agents/backend.py

This simple Flask server bridges your HTML UI to your working agents.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Import your working agents
from agents import run_ops_mode, run_traveler_mode, call_mcp_list_region

app = Flask(__name__)
CORS(app)  # Enable CORS for browser requests

# ============================================
# API Endpoints for Frontend
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if backend is running."""
    return jsonify({
        "status": "ok",
        "message": "Backend is running"
    })

@app.route('/api/ops/analyze', methods=['POST'])
def analyze_ops():
    """
    Operations Mode: Analyze a region
    Expected JSON: {"region": "region1"}
    """
    try:
        data = request.get_json()
        region = data.get('region', 'region1')
        
        print(f"[API] Analyzing region: {region}")
        
        # Call your working agents.py function
        result = run_ops_mode(region)
        
        # Format response for frontend
        response = {
            "success": True,
            "region": result['region'],
            "timestamp": result.get('timestamp', 'N/A'),
            "total_flights": result['total_flights'],
            "anomalous_flights": result['anomalous_flights'],
            "analysis": result['analysis'],
            "flights": result['raw_data']['all_flights'],
            "alerts": result['raw_data']['alerts']
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[API ERROR] Ops analysis failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/traveler/track', methods=['POST'])
def track_flight():
    """
    Traveler Mode: Track a specific flight
    Expected JSON: {"flight_id": "UAL321"}
    """
    try:
        data = request.get_json()
        flight_id = data.get('flight_id', '').strip()
        
        if not flight_id:
            return jsonify({
                "success": False,
                "error": "Flight ID is required"
            }), 400
        
        print(f"[API] Tracking flight: {flight_id}")
        
        # Call your working agents.py function
        result = run_traveler_mode(flight_id)
        
        # Check if flight was found
        if "error" in str(result.get("summary", "")).lower() or "could not find" in str(result.get("summary", "")).lower():
            return jsonify({
                "success": False,
                "error": f"Flight {flight_id} not found"
            }), 404
        
        # Format response for frontend
        response = {
            "success": True,
            "flight_id": flight_id,
            "summary": result['summary'],
            "issues": result['issues'],
            "raw_data": result.get('raw_data', {})
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[API ERROR] Flight tracking failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/traveler/ask', methods=['POST'])
def ask_question():
    """
    Traveler Mode: Ask a question about a flight
    Expected JSON: {"flight_id": "UAL321", "question": "Where is my flight?"}
    """
    try:
        data = request.get_json()
        flight_id = data.get('flight_id', '').strip()
        question = data.get('question', '').strip()
        
        if not flight_id or not question:
            return jsonify({
                "success": False,
                "error": "Both flight_id and question are required"
            }), 400
        
        print(f"[API] Question about {flight_id}: {question}")
        
        # Call your working agents.py function with question
        result = run_traveler_mode(flight_id, question)
        
        # Format response for frontend
        response = {
            "success": True,
            "flight_id": flight_id,
            "question": question,
            "answer": result.get('qa_response', 'Could not generate answer'),
            "raw_data": result.get('raw_data', {})
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"[API ERROR] Question answering failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/flights/list', methods=['GET'])
def list_all_flights():
    """
    Get all flights from MCP (for debugging/testing)
    """
    try:
        region = request.args.get('region', 'region1')
        data = call_mcp_list_region(region)
        
        if "error" in data:
            return jsonify({
                "success": False,
                "error": data["error"]
            }), 500
        
        return jsonify({
            "success": True,
            "flights": data.get("flights", [])
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

# ============================================
# Main
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AIRSPACE COPILOT - BACKEND API SERVER")
    print("="*60)
    print("\n📡 API Endpoints Available:")
    print("   GET  /api/health           - Health check")
    print("   POST /api/ops/analyze      - Operations analysis")
    print("   POST /api/traveler/track   - Track flight")
    print("   POST /api/traveler/ask     - Ask question")
    print("   GET  /api/flights/list     - List all flights")
    print("\n🌐 Starting server on http://localhost:5000")
    print("="*60 + "\n")
    
    # Run Flask server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )