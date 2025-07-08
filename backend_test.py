import requests
import json
import unittest
import os
import sys
from datetime import datetime

# Get the backend URL from frontend/.env
BACKEND_URL = "https://b99b4e23-5bc0-444f-b40b-b14646e6bbb5.preview.emergentagent.com/api"

class LinkedInAIAutomationBackendTest(unittest.TestCase):
    """Test suite for LinkedIn AI Automation Backend"""

    def test_01_root_endpoint(self):
        """Test the root endpoint"""
        print("\n=== Testing Root Endpoint ===")
        response = requests.get(f"{BACKEND_URL}/")
        print(f"Response: {response.status_code} - {response.text}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "LinkedIn AI Automation System")
        print("✅ Root endpoint test passed")

    def test_02_openai_integration(self):
        """Test OpenAI integration"""
        print("\n=== Testing OpenAI Integration ===")
        response = requests.get(f"{BACKEND_URL}/test/openai")
        print(f"Response: {response.status_code} - {response.text}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check if there's an error with the API key
        if data["status"] == "error":
            print(f"❌ OpenAI integration test failed: {data.get('error', 'Unknown error')}")
            # Print detailed error for debugging
            if "Incorrect API key provided" in str(data.get('error', '')):
                print("The API key format appears to be incorrect or the key has been revoked.")
                print("This is using a project-based API key with 'sk-proj-' prefix which requires the latest OpenAI library.")
            self.fail(f"OpenAI API error: {data.get('error', 'Unknown error')}")
        else:
            self.assertEqual(data["status"], "success")
            print("✅ OpenAI integration test passed")

    def test_03_ollama_integration(self):
        """Test Ollama integration (might fail if Ollama is not running locally)"""
        print("\n=== Testing Ollama Integration ===")
        response = requests.get(f"{BACKEND_URL}/test/ollama")
        print(f"Response: {response.status_code} - {response.text}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # This might fail if Ollama is not running locally, which is expected
        print(f"Ollama test result: {data['status']}")
        if data["status"] == "error":
            print("⚠️ Ollama integration test failed (expected if Ollama is not running locally)")
        else:
            print("✅ Ollama integration test passed")

    def test_04_target_management(self):
        """Test target management (create and get targets)"""
        print("\n=== Testing Target Management ===")
        
        # Create a test target
        target_data = {
            "name": "John Smith",
            "title": "AI Research Scientist",
            "company": "TechCorp AI",
            "linkedin_url": "https://linkedin.com/in/johnsmith",
            "email": "john.smith@example.com",
            "location": "San Francisco, CA",
            "profile_summary": "AI researcher with 10+ years of experience in machine learning and neural networks.",
            "recent_activity": "Published a paper on transformer models for NLP applications."
        }
        
        # Test creating a target
        print("Creating a target...")
        create_response = requests.post(f"{BACKEND_URL}/targets", json=target_data)
        print(f"Create Response: {create_response.status_code}")
        self.assertEqual(create_response.status_code, 200)
        created_target = create_response.json()
        self.assertEqual(created_target["name"], target_data["name"])
        self.assertEqual(created_target["title"], target_data["title"])
        self.assertEqual(created_target["company"], target_data["company"])
        target_id = created_target["id"]
        print(f"Created target with ID: {target_id}")
        
        # Test getting all targets
        print("Getting all targets...")
        get_response = requests.get(f"{BACKEND_URL}/targets")
        print(f"Get Response: {get_response.status_code}")
        self.assertEqual(get_response.status_code, 200)
        targets = get_response.json()
        self.assertIsInstance(targets, list)
        # Check if our created target is in the list
        target_found = False
        for target in targets:
            if target["id"] == target_id:
                target_found = True
                break
        self.assertTrue(target_found, "Created target not found in targets list")
        print("✅ Target management tests passed")
        
        return target_id  # Return the target ID for use in other tests

    def test_05_message_generation(self):
        """Test message generation using OpenAI"""
        print("\n=== Testing Message Generation ===")
        
        # First create a target to use for message generation
        target_id = self.test_04_target_management()
        
        # Prepare message generation request
        message_request = {
            "target_id": target_id,
            "profile_data": {
                "name": "John Smith",
                "title": "AI Research Scientist",
                "company": "TechCorp AI",
                "profile_summary": "AI researcher with 10+ years of experience in machine learning and neural networks.",
                "recent_activity": "Published a paper on transformer models for NLP applications."
            },
            "message_type": "connection_request",
            "llm_provider": "openai",
            "model": "gpt-4"
        }
        
        # Test generating a message
        print("Generating a personalized message...")
        response = requests.post(f"{BACKEND_URL}/messages/generate", json=message_request)
        print(f"Response: {response.status_code}")
        
        if response.status_code == 200:
            message = response.json()
            print(f"Generated message: {message['content'][:100]}...")
            self.assertIsNotNone(message["content"])
            self.assertTrue(len(message["content"]) > 0)
            self.assertEqual(message["target_id"], target_id)
            print("✅ Message generation test passed")
        else:
            print(f"Error response: {response.text}")
            # Try to get more detailed error information
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print("Could not parse error response as JSON")
            
            # Check if this is related to the OpenAI API key issue
            if response.status_code == 500:
                print("This failure is likely related to the OpenAI API key issue.")
                print("The message generation endpoint uses the same OpenAI client as the test endpoint.")
            
            self.fail("Message generation failed")

    def test_06_analytics(self):
        """Test analytics endpoint"""
        print("\n=== Testing Analytics ===")
        response = requests.get(f"{BACKEND_URL}/analytics")
        print(f"Response: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        analytics = response.json()
        
        # Check that all required fields are present
        required_fields = [
            "total_targets", "connections_sent", "connections_accepted",
            "messages_sent", "messages_replied", "acceptance_rate",
            "reply_rate", "daily_activity"
        ]
        
        for field in required_fields:
            self.assertIn(field, analytics)
            
        # Check that daily_activity is a dictionary
        self.assertIsInstance(analytics["daily_activity"], dict)
        
        print("✅ Analytics test passed")

if __name__ == "__main__":
    # Run the tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)