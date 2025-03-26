import requests
import json
from datetime import datetime

def test_registration():
    base_url = "http://localhost:5000"
    
    # Generate unique email using timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_email = f"testuser{timestamp}@example.com"
    
    print("1. Testing basic GET request without headers...")
    try:
        response = requests.get(f"{base_url}/register")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n2. Testing GET request with headers...")
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "http://localhost:5173"
        }
        response = requests.get(f"{base_url}/register", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n3. Testing POST request...")
    try:
        data = {
            "username": f"testuser{timestamp}",
            "email": unique_email,
            "password": "Test@password123",
            "date_of_birth": "1990-01-01",
            "gender": "other",
            "country_code": "+1"
        }
        print(f"Request data: {json.dumps(data, indent=2)}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        
        response = requests.post(f"{base_url}/register", json=data, headers=headers)
        print(f"\nStatus: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content: {json.dumps(response.json(), indent=2)}")
        
        response_data = response.json()
        print(f"\nParsed response: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 200 and response_data.get("success"):
            print("\n✓ Registration successful!")
            print(f"User ID: {response_data['user']['user_id']}")
            print(f"Username: {response_data['user']['username']}")
            print(f"Email: {response_data['user']['email']}")
        else:
            print("\n❌ Registration failed!")
            print(f"Error: {response_data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    test_registration() 