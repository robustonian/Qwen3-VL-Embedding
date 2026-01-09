#!/usr/bin/env python3
"""
Test script for the Qwen3-VL Embedding API server.
Tests various input types including text, images (URL, relative path, absolute path), and mixed inputs.
"""

import os
import json
import requests
import time
from pathlib import Path

API_BASE = "http://localhost:8000"
TEST_IMAGE_URL = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{API_BASE}/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_models():
    """Test models endpoint"""
    print("\nTesting models endpoint...")
    response = requests.get(f"{API_BASE}/v1/models")
    print(f"Models: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_text_embedding():
    """Test simple text embedding"""
    print("\nTesting text embedding...")
    payload = {
        "input": "Hello, world!",
        "model": "qwen3-vl-embedding"
    }
    response = requests.post(f"{API_BASE}/v1/embeddings", json=payload)
    result = response.json()
    
    if response.status_code == 200:
        print(f"Text embedding success. Dimension: {len(result['data'][0]['embedding'])}")
        return True
    else:
        print(f"Text embedding failed: {response.status_code} - {result}")
        return False

def test_batch_text_embedding():
    """Test batch text embedding"""
    print("\nTesting batch text embedding...")
    payload = {
        "input": [
            "Hello, world!",
            "This is a test sentence.",
            "Another example text."
        ],
        "model": "qwen3-vl-embedding"
    }
    response = requests.post(f"{API_BASE}/v1/embeddings", json=payload)
    result = response.json()
    
    if response.status_code == 200:
        print(f"Batch text embedding success. Got {len(result['data'])} embeddings")
        return True
    else:
        print(f"Batch text embedding failed: {response.status_code} - {result}")
        return False

def test_image_url_embedding():
    """Test image embedding from URL"""
    print("\nTesting image URL embedding...")
    payload = {
        "input": TEST_IMAGE_URL,
        "model": "qwen3-vl-embedding"
    }
    response = requests.post(f"{API_BASE}/v1/embeddings", json=payload)
    result = response.json()
    
    if response.status_code == 200:
        print(f"Image URL embedding success. Dimension: {len(result['data'][0]['embedding'])}")
        return True
    else:
        print(f"Image URL embedding failed: {response.status_code} - {result}")
        return False

def test_image_relative_path():
    """Test image embedding from relative path"""
    print("\nTesting image relative path embedding...")
    test_image_path = "data/examples/0.jpeg"
    
    if not os.path.exists(test_image_path):
        print(f"Test image not found at {test_image_path}, skipping...")
        return True
    
    payload = {
        "input": test_image_path,
        "model": "qwen3-vl-embedding"
    }
    response = requests.post(f"{API_BASE}/v1/embeddings", json=payload)
    result = response.json()
    
    if response.status_code == 200:
        print(f"Image relative path embedding success. Dimension: {len(result['data'][0]['embedding'])}")
        return True
    else:
        print(f"Image relative path embedding failed: {response.status_code} - {result}")
        return False

def test_image_absolute_path():
    """Test image embedding from absolute path"""
    print("\nTesting image absolute path embedding...")
    test_image_path = os.path.abspath("data/examples/0.jpeg")
    
    if not os.path.exists(test_image_path):
        print(f"Test image not found at {test_image_path}, skipping...")
        return True
    
    payload = {
        "input": test_image_path,
        "model": "qwen3-vl-embedding"
    }
    response = requests.post(f"{API_BASE}/v1/embeddings", json=payload)
    result = response.json()
    
    if response.status_code == 200:
        print(f"Image absolute path embedding success. Dimension: {len(result['data'][0]['embedding'])}")
        return True
    else:
        print(f"Image absolute path embedding failed: {response.status_code} - {result}")
        return False

def test_mixed_input():
    """Test mixed text and image input"""
    print("\nTesting mixed input (text + image)...")
    payload = {
        "input": [
            "This is a text example.",
            TEST_IMAGE_URL,
            {
                "text": "A woman playing with her dog on a beach.",
                "image": TEST_IMAGE_URL,
                "instruction": "Describe this image."
            }
        ],
        "model": "qwen3-vl-embedding"
    }
    response = requests.post(f"{API_BASE}/v1/embeddings", json=payload)
    result = response.json()
    
    if response.status_code == 200:
        print(f"Mixed input embedding success. Got {len(result['data'])} embeddings")
        for i, data in enumerate(result['data']):
            print(f"  Embedding {i}: dimension {len(data['embedding'])}")
        return True
    else:
        print(f"Mixed input embedding failed: {response.status_code} - {result}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\nTesting error handling...")
    
    # Test invalid model
    payload = {
        "input": "Test",
        "model": "invalid-model"
    }
    response = requests.post(f"{API_BASE}/v1/embeddings", json=payload)
    if response.status_code != 422:
        print(f"Expected 422 for invalid model, got {response.status_code}")
        return False
    
    # Test empty input
    payload = {
        "input": "",
        "model": "qwen3-vl-embedding"
    }
    response = requests.post(f"{API_BASE}/v1/embeddings", json=payload)
    # Should still work, just return embedding for empty text
    
    print("Error handling tests passed")
    return True

def main():
    """Run all tests"""
    print("Starting API tests...")
    print("Make sure the API server is running on http://localhost:8000")
    
    # Wait a bit for server to be ready
    time.sleep(2)
    
    tests = [
        test_health,
        test_models,
        test_text_embedding,
        test_batch_text_embedding,
        test_image_url_embedding,
        test_image_relative_path,
        test_image_absolute_path,
        test_mixed_input,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_func.__name__} failed")
        except Exception as e:
            print(f"❌ {test_func.__name__} failed with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    
    return passed == total

if __name__ == "__main__":
    main()