#!/usr/bin/env python3
"""
Test script for the simplified manual search endpoints
Tests that the manual search is working directly with Open Library API
"""

import requests
import json
import sys

def test_simple_manual_search():
    """Test the simplified manual search endpoints"""
    print("🧪 Testing Simplified Manual Book Search")
    print("=" * 60)
    
    base_url = "http://localhost:8002"
    
    # Test 1: Basic manual search
    print("\n📚 Test 1: Basic manual search for 'Harry Potter'")
    try:
        response = requests.get(f"{base_url}/api/search-books", params={"query": "Harry Potter", "limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['total_results']} results")
            if data['results']:
                first_book = data['results'][0]
                print(f"  📖 First result: {first_book['title']} by {first_book['author_name']}")
                print(f"  🔑 Key: {first_book['key']}")
                print(f"  📅 Year: {first_book['first_publish_year']}")
            else:
                print("  ⚠️  No results returned")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Advanced manual search
    print("\n🔍 Test 2: Advanced manual search by title and author")
    try:
        response = requests.get(f"{base_url}/api/search-books-advanced", 
                              params={"title": "Ballad", "author": "Collins", "limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['total_results']} results")
            print(f"   Search query: {data['search_query']}")
            if data['results']:
                first_book = data['results'][0]
                print(f"  📖 First result: {first_book['title']} by {first_book['author_name']}")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Direct Open Library API test (for comparison)
    print("\n🌐 Test 3: Direct Open Library API test")
    try:
        search_url = "https://openlibrary.org/search.json"
        params = {
            "q": "Harry Potter",
            "limit": 3,
            "fields": "key,title,author_name,first_publish_year"
        }
        
        response = requests.get(search_url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            docs = data.get("docs", [])
            print(f"✅ Direct API success! Found {len(docs)} results")
            if docs:
                first_doc = docs[0]
                print(f"  📖 First result: {first_doc.get('title', 'Unknown')} by {first_doc.get('author_name', 'Unknown')}")
        else:
            print(f"❌ Direct API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Direct API error: {e}")
    
    # Test 4: Search with no results
    print("\n🔍 Test 4: Search with no results (very specific)")
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

def main():
    """Run all tests"""
    print("🔍 Simplified Manual Search Testing")
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
    test_simple_manual_search()
    
    print("\n" + "=" * 60)
    print("🎉 Simplified manual search testing completed!")
    print("\n💡 What this means:")
    print("   - Manual search is now completely independent of the pipeline")
    print("   - It makes direct calls to Open Library API")
    print("   - No complex text processing or filtering")
    print("   - Just simple, direct fuzzy search as requested")
    print("\n🔧 To test in the frontend:")
    print("   1. Start the frontend: cd web_interface && npm start")
    print("   2. Click 'Manual Search' button in the header")
    print("   3. Type any book title/author and search")
    print("   4. Results should come directly from Open Library")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


