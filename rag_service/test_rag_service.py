import requests
import json
import time
import sys

def test_rag_service():
    """Test the RAG service running in Docker."""
    url = "http://localhost:8000/chat"
    
    # Test query
    payload = {
        "question": "What is the role of a District Absence Coordinator?"
    }
    
    print("Testing RAG service at", url)
    print("Sending query:", payload["question"])
    
    max_retries = 5
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            print("\n✅ RAG Service Test Successful!")
            print("\nResponse:")
            print(json.dumps(result, indent=2))
            return True
            
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                print(f"Connection failed. Retrying in {retry_delay} seconds ({i+1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print("\n❌ Connection Error: Cannot connect to RAG service")
                print("Make sure the Docker container is running on port 8000")
                return False
                
        except requests.exceptions.HTTPError as e:
            print(f"\n❌ HTTP Error: {e}")
            return False
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

if __name__ == "__main__":
    success = test_rag_service()
    if not success:
        sys.exit(1)
