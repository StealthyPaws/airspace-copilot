"""
Simple Test Script - Test your system without UI
File: agents/simple_test.py
Run this first to verify everything works before using the full UI
"""

import os
from agents import run_ops_mode, run_traveler_mode, call_mcp_list_region

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_mcp_connection():
    """Test if MCP server is accessible."""
    print_section("TEST 1: MCP Server Connection")
    
    try:
        data = call_mcp_list_region("region1")
        if "error" in data:
            print("❌ MCP Server Error:", data["error"])
            print("\n📝 Fix: Make sure MCP server is running:")
            print("   cd mcp")
            print("   python mcp_server.py")
            return False
        else:
            flights = data.get("flights", [])
            print(f"✅ MCP Server is working!")
            print(f"   Found {len(flights)} flights in region1")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n📝 Fix: Start the MCP server first")
        return False

def test_ops_mode():
    """Test operations mode."""
    print_section("TEST 2: Operations Mode")
    
    try:
        result = run_ops_mode("region1")
        print(f"✅ Ops Mode Working!")
        print(f"\n📊 Statistics:")
        print(f"   Region: {result['region']}")
        print(f"   Total Flights: {result['total_flights']}")
        print(f"   Anomalous Flights: {result['anomalous_flights']}")
        print(f"\n🤖 AI Analysis:")
        print(f"   {result['analysis'][:300]}...")
        
        return result
    except Exception as e:
        print(f"❌ Ops Mode failed: {e}")
        return None

def test_traveler_mode(ops_result):
    """Test traveler mode with a real flight."""
    print_section("TEST 3: Traveler Mode")
    
    if not ops_result or ops_result['total_flights'] == 0:
        print("⚠️  No flights available for testing")
        return
    
    # Get first available flight
    test_flight = ops_result['raw_data']['all_flights'][0]
    test_callsign = (test_flight.get('callsign') or test_flight.get('icao24') or "").strip()
    
    if not test_callsign:
        print("⚠️  Could not find valid callsign")
        return
    
    print(f"🔍 Testing with flight: {test_callsign}")
    
    try:
        result = run_traveler_mode(test_callsign)
        print(f"✅ Traveler Mode Working!")
        print(f"\n📍 Flight Info:")
        print(f"   {result['summary'][:250]}...")
        print(f"\n⚠️  Issues Check:")
        print(f"   {result['issues']}")
        
        return test_callsign
    except Exception as e:
        print(f"❌ Traveler Mode failed: {e}")
        return None

def test_qa_mode(callsign):
    """Test Q&A with A2A communication."""
    print_section("TEST 4: Q&A with A2A Communication")
    
    if not callsign:
        print("⚠️  Skipping - no valid callsign")
        return
    
    question = "Are there any other flights nearby having issues?"
    print(f"❓ Question: {question}")
    
    try:
        result = run_traveler_mode(callsign, question)
        answer = result.get('qa_response', 'No answer')
        print(f"\n💬 Answer:")
        print(f"   {answer[:300]}...")
        print("\n✅ Q&A Mode Working!")
        print("   (Notice: Traveler agent called Ops agent for context)")
    except Exception as e:
        print(f"❌ Q&A failed: {e}")

def check_groq_key():
    """Check if Groq API key is set."""
    print_section("CHECKING CONFIGURATION")
    
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key or groq_key == "KEY":
        print("⚠️  WARNING: GROQ_API_KEY not found!")
        print("\n📝 To fix:")
        print("   1. Create a .env file in the agents folder")
        print("   2. Add: GROQ_API_KEY=gsk_your_actual_key")
        print("   3. Or edit agents.py and set it directly")
        print("\nContinuing test (will fail at LLM calls)...\n")
        return False
    else:
        print("✅ GROQ_API_KEY is set")
        print(f"   Key: {groq_key[:20]}...")
        return True

def main():
    """Run all tests."""
    print("\n")
    print("🚀 " + "="*66 + " 🚀")
    print("   AIRSPACE COPILOT - SYSTEM TEST")
    print("🚀 " + "="*66 + " 🚀")
    
    # Check configuration
    has_key = check_groq_key()
    
    # Test MCP connection
    if not test_mcp_connection():
        print("\n❌ Cannot proceed without MCP server")
        print("\n💡 Start MCP server first:")
        print("   cd mcp")
        print("   python mcp_server.py")
        return
    
    if not has_key:
        print("\n⚠️  Tests will fail without Groq API key")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Test ops mode
    ops_result = test_ops_mode()
    
    # Test traveler mode
    callsign = test_traveler_mode(ops_result)
    
    # Test Q&A
    test_qa_mode(callsign)
    
    # Final summary
    print_section("TEST SUMMARY")
    print("✅ All components tested!")
    print("\n📝 Next steps:")
    print("   1. If all tests passed, run the full UI:")
    print("      streamlit run app.py")
    print("\n   2. If tests failed, check the error messages above")
    print("      and follow the fix instructions")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main()