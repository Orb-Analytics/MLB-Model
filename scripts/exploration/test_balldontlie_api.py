"""
Test script for Balldontlie.io MLB API
Run this to verify your API key is working correctly

Works in both environments:
- Locally: reads from .env file
- GitHub Actions: reads from repository secrets
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# Get API key from environment (works for both .env and GitHub Actions)
API_KEY = os.getenv('BALLDONTLIE_API_KEY')

if not API_KEY:
    print("❌ Error: BALLDONTLIE_API_KEY not found in environment variables")
    print("Please create a .env file and add your API key:")
    print("BALLDONTLIE_API_KEY=your_api_key_here")
    exit(1)

# Base URL for Balldontlie API
BASE_URL = "https://api.balldontlie.io/v1"

def test_api_connection():
    """Test basic API connectivity"""
    print("Testing Balldontlie.io API connection...")
    print(f"API Key (first 10 chars): {API_KEY[:10]}...")
    
    # Test endpoint - update this based on Balldontlie API documentation
    # Common endpoints might be: /teams, /games, /players, etc.
    headers = {
        "Authorization": API_KEY
    }
    
    # Try teams endpoint
    endpoints_to_test = [
        "/mlb/teams",
        "/teams", 
        "/games"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\n🔍 Testing endpoint: {endpoint}")
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success! API is working")
                data = response.json()
                print(f"Response preview: {str(data)[:200]}...")
                return True
            elif response.status_code == 401:
                print("❌ Authentication failed - check your API key")
            elif response.status_code == 404:
                print("⚠️  Endpoint not found - trying next one...")
                continue
            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    print("\n❌ None of the test endpoints worked.")
    print("Please check the Balldontlie API documentation for correct endpoints.")
    return False

if __name__ == "__main__":
    test_api_connection()
