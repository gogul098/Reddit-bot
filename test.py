import requests
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
# Adjust the payload to match the Pydantic schema you defined in Phase 2
MOCK_PAYLOAD = {
    "post_id": "test_reddit_post_001",
    "title": "A highly controversial debate about Python vs. Java",
    "comments": [
        {"id": "c1", "author": "userA", "body": "Python is too slow for real backend work.", "score": 10},
        {"id": "c2", "author": "userB", "body": "You clearly don't understand how async works.", "score": -5}
    ]
}

def run_handshake_test():
    print("🚀 Initiating Asynchronous Handshake Test...")
    print("-" * 50)
    
    # STEP 1: Fire and Forget (The Initial POST)
    print("📡 Step 1: Sending payload to Django API Gateway...")
    try:
        response = requests.post(f"{BASE_URL}/analyze/", json=MOCK_PAYLOAD)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to Django. Is runserver running?")
        sys.exit(1)

    data = response.json()
    task_id = data.get("task_id")
    
    if not task_id:
        print("❌ ERROR: Django did not return a task_id. Check your API response structure.")
        sys.exit(1)
        
    print(f"✅ Success! Django accepted the payload and returned Task ID: {task_id}")
    print(f"   (This proves Django successfully handed the task to Redis DB 0)\n")

    # STEP 2: The Polling Loop
    print("⏳ Step 2: Polling the Status Endpoint (Waiting for Celery...)")
    max_attempts = 15
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        status_response = requests.get(f"{BASE_URL}/status/{task_id}/")
        status_data = status_response.json()
        
        current_state = status_data.get("status")
        print(f"   [Poll {attempts}/{max_attempts}] Current State: {current_state}")
        
        if current_state == "SUCCESS":
            print("\n🎉 HANDSHAKE COMPLETE! Celery successfully processed the task.")
            print("-" * 50)
            print("Final Output from Redis DB 1:")
            print(status_data.get("result", "No result payload found."))
            break
            
        elif current_state == "FAILURE":
            print("\n❌ TASK FAILED! Celery encountered an error.")
            print(f"Reason: {status_data.get('error', 'Unknown')}")
            break
            
        # Wait 3 seconds before pinging again, exactly like Devvit will
        time.sleep(3)
        
    if attempts == max_attempts:
        print("\n⚠️ TIMEOUT: Task did not complete in time. Check your Celery worker logs.")

if __name__ == "__main__":
    run_handshake_test()