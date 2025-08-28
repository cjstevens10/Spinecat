#!/usr/bin/env python3
"""
Test script for the manual search API endpoints
Tests the new manual book search functionality for users
"""

import requests
import json
import sys

def test_manual_search():
    """Test the basic manual search endpoint"""
    print("🔍 Testing Manual Book Search API")
    print("=" * 50)
    
    base_url = "http://localhost:8002"
    
    # Test 1: Basic search
    print("\n📚 Test 1: Basic search for 'Harry Potter'")
    try:
        response = requests.get(f"{base_url}/api/search-books", params={"query": "Harry Potter", "limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['total_results']} results")
            for i, book in enumerate(data['results'][:3], 1):
                print(f"  {i}. {book['title']} by {book['author_name']}")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Advanced search by title and author
    print("\n🔍 Test 2: Advanced search by title and author")
    try:
        response = requests.get(f"{base_url}/api/search-books-advanced", 
                              params={"title": "Ballad", "author": "Collins", "limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['total_results']} results")
            print(f"   Search query: {data['search_query']}")
            for i, book in enumerate(data['results'][:3], 1):
                print(f"  {i}. {book['title']} by {book['author_name']}")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Search with no results
    print("\n🔍 Test 3: Search with no results (very specific)")
    try:
        response = requests.get(f"{base_url}/api/search-books", 
                              params={"query": "ThisBookDefinitelyDoesNotExist12345", "limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['total_results']} results (expected 0)")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Invalid search (too short)
    print("\n🔍 Test 4: Invalid search (too short)")
    try:
        response = requests.get(f"{base_url}/api/search-books", params={"query": "A", "limit": 5})
        if response.status_code == 400:
            print("✅ Successfully rejected short query")
        else:
            print(f"❌ Should have rejected short query, got status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_search_parameters():
    """Test different search parameter combinations"""
    print("\n🔍 Testing Search Parameters")
    print("=" * 50)
    
    base_url = "http://localhost:8002"
    
    test_cases = [
        {"title": "Great Gatsby", "author": "", "publisher": ""},
        {"title": "", "author": "Fitzgerald", "publisher": ""},
        {"title": "1984", "author": "Orwell", "publisher": ""},
        {"title": "", "author": "", "publisher": "Penguin"},
        {"title": "Pride", "author": "Austen", "publisher": "Penguin"}
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n📚 Test Case {i}: {params}")
        try:
            response = requests.get(f"{base_url}/api/search-books-advanced", params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Found {data['total_results']} results")
                if data['results']:
                    first_result = data['results'][0]
                    print(f"  📖 First: {first_result['title']} by {first_result['author_name']}")
            else:
                print(f"  ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

def main():
    """Run all manual search tests"""
    print("🧪 Testing Manual Book Search Functionality")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8002/health")
        if response.status_code != 200:
            print("❌ Backend is not running. Please start the backend first:")
            print("   cd web_interface/backend && python main.py")
            return False
        print("✅ Backend is running")
    except Exception as e:
        print("❌ Cannot connect to backend. Please start it first:")
        print("   cd web_interface/backend && python main.py")
        return False
    
    # Run tests
    test_manual_search()
    test_search_parameters()
    
    print("\n" + "=" * 60)
    print("🎉 Manual search testing completed!")
    print("\n💡 API Endpoints Available:")
    print("   - GET /api/search-books?query=<search_term>&limit=<number>")
    print("   - GET /api/search-books-advanced?title=<title>&author=<author>&publisher=<publisher>&limit=<number>")
    print("\n📖 Use these endpoints to let users manually search for books when OCR fails!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


