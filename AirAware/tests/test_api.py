
import requests
import sys
import json

def test_api():
    try:
        # Assuming local server is running on port 5000
        response = requests.get('http://127.0.0.1:5000/api/map-data')
        
        if response.status_code != 200:
            print(f"FAILED: Status code {response.status_code}")
            return False
            
        data = response.json()
        
        if 'cities' not in data:
            print("FAILED: 'cities' key missing in response")
            return False
            
        cities = data['cities']
        print(f"Success: Fetched {len(cities)} cities.")
        
        if len(cities) == 0:
            print("WARNING: No cities returned.")
            return True # It's a valid response, just empty
            
        # Check first city structure
        city = cities[0]
        required_fields = ['name', 'lat', 'lng', 'aqi', 'color', 'category']
        
        missing = [f for f in required_fields if f not in city]
        
        if missing:
            print(f"FAILED: Missing fields in city object: {missing}")
            return False
            
        print(f"Sample City: {city['name']}, AQI: {city['aqi']}, Category: {city['category']}")
        print("VERIFICATION PASSED")
        return True
        
    except requests.exceptions.ConnectionError:
        print("FAILED: Could not connect to server. Make sure Flask app is running.")
        return False
    except Exception as e:
        print(f"FAILED: Error - {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
