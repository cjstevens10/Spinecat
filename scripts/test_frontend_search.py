#!/usr/bin/env python3
"""
Test script to verify the frontend manual search functionality
Tests the API endpoints that the frontend uses
"""

import requests
import json
import sys

def test_manual_search_api():
    """Test the manual search API endpoints"""
    print("🧪 Testing Frontend Manual Search API")
    print("=" * 60)
    
    base_url = "http://localhost:8002"
    
    # Test 1: Basic search endpoint
    print("\n📚 Test 1: Basic search endpoint")
    try:
        response = requests.get(f"{base_url}/api/search-books", params={"query": "Harry Potter", "limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total_results', len(data.get('results', [])))} results")
            if 'results' in data and data['results']:
                first_book = data['results'][0]
                print(f"  📖 First result: {first_book.get('title', 'Unknown')} by {first_book.get('author_name', 'Unknown')}")
            else:
                print("  ⚠️  No results in response")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Advanced search endpoint
    print("\n🔍 Test 2: Advanced search endpoint")
    try:
        response = requests.get(f"{base_url}/api/search-books-advanced", 
                              params={"title": "Ballad", "author": "Collins", "limit": 5})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total_results', len(data.get('results', [])))} results")
            if 'results' in data and data['results']:
                first_book = data['results'][0]
                print(f"  📖 First result: {first_book.get('title', 'Unknown')} by {first_book.get('author_name', 'Unknown')}")
            else:
                print("  ⚠️  No results in response")
        else:
            print(f"❌ Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Health check
    print("\n🏥 Test 3: Backend health check")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data}")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Frontend accessibility
    print("\n🌐 Test 4: Frontend accessibility")
    try:
        response = requests.get("http://localhost:3000")
        if response.status_code == 200:
            print("✅ Frontend is accessible at http://localhost:3000")
        else:
            print(f"❌ Frontend returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        print("   Make sure to run: cd web_interface && npm start")

def main():
    """Run all tests"""
    print("🔍 Frontend Manual Search Testing")
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
    test_manual_search_api()
    
    print("\n" + "=" * 60)
    print("🎉 Frontend manual search testing completed!")
    print("\n💡 What to test in the frontend:")
    print("   1. Click 'Manual Search' button in the header")
    print("   2. Try basic search with 'Harry Potter'")
    print("   3. Try advanced search with title='Ballad', author='Collins'")
    print("   4. Click 'Search Open Library' in BookListManager")
    print("   5. Click 'Search & Add' on OCR failures")
    print("\n🔧 If search isn't working:")
    print("   - Check browser console for errors")
    print("   - Verify backend is running on port 8002")
    print("   - Check that the search API endpoints return data")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


