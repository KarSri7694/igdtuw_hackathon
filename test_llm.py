"""
Test script for LLM privacy analysis functionality
Run this to test if the LLM server is working correctly for privacy analysis
"""

from llm import LlamaCppClient
import json


def test_llm_connection():
    """Test basic LLM server connection"""
    print("=" * 80)
    print("TEST 1: LLM Server Connection")
    print("=" * 80)
    
    client = LlamaCppClient(base_url="http://localhost:8080")
    
    if client.check_server_status():
        print("✅ LLM server is running and accessible")
        return client
    else:
        print("❌ LLM server is not responding")
        print("\nPlease start the llama.cpp server:")
        print("  llama-server -m models/qwen-model.gguf --port 8080")
        return None


def test_simple_query(client):
    """Test basic query functionality"""
    print("\n" + "=" * 80)
    print("TEST 2: Simple Query")
    print("=" * 80)
    
    try:
        response = client.simple_query(
            query="What is 2+2?",
            system_prompt="You are a helpful assistant. Answer briefly."
        )
        print(f"✅ Query successful")
        print(f"Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False


def test_json_extraction(client):
    """Test JSON extraction from LLM response"""
    print("\n" + "=" * 80)
    print("TEST 3: JSON Response Parsing")
    print("=" * 80)
    
    test_cases = [
        '{"test": "value"}',
        '```json\n{"test": "value"}\n```',
        '```\n{"test": "value"}\n```',
        'Here is the JSON: {"test": "value"} - that\'s it!',
    ]
    
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        try:
            result = client._extract_json_from_response(test_case)
            print(f"✅ Test case {i} passed: {result}")
        except Exception as e:
            print(f"❌ Test case {i} failed: {e}")
            all_passed = False
    
    return all_passed


def test_privacy_analysis_safe(client):
    """Test privacy analysis with safe text (no sensitive info)"""
    print("\n" + "=" * 80)
    print("TEST 4: Privacy Analysis - Safe Text")
    print("=" * 80)
    
    safe_text = "The weather is nice today. I went for a walk in the park."
    
    try:
        result = client.analyze_privacy(
            text=safe_text,
            filename="weather_note.txt"
        )
        
        print(f"✅ Analysis completed")
        print(f"Contains Sensitive Info: {result.get('contains_sensitive_info')}")
        print(f"Risk Level: {result.get('risk_level')}")
        print(f"Expected: risk_level should be 'none' or 'low'")
        
        if result.get('risk_level') in ['none', 'low']:
            print("✅ Risk level is appropriate for safe text")
            return True
        else:
            print(f"⚠️  Unexpected risk level: {result.get('risk_level')}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


def test_privacy_analysis_sensitive(client):
    """Test privacy analysis with sensitive information"""
    print("\n" + "=" * 80)
    print("TEST 5: Privacy Analysis - Sensitive Text")
    print("=" * 80)
    
    sensitive_text = """
    John Doe
    SSN: 123-45-6789
    Phone: (555) 123-4567
    Email: john.doe@email.com
    Credit Card: 4532 1234 5678 9010
    """
    
    try:
        result = client.analyze_privacy(
            text=sensitive_text,
            filename="id_document.jpg"
        )
        
        print(f"✅ Analysis completed")
        print(f"Contains Sensitive Info: {result.get('contains_sensitive_info')}")
        print(f"Risk Level: {result.get('risk_level')}")
        print(f"Detected Categories: {result.get('detected_categories', [])}")
        print(f"Specific Findings: {result.get('specific_findings', [])[:3]}")
        print(f"Recommendations: {result.get('recommendations', [])[:2]}")
        
        if result.get('contains_sensitive_info') and result.get('risk_level') in ['high', 'critical']:
            print("✅ Correctly identified sensitive information")
            return True
        else:
            print(f"⚠️  May have missed sensitive information")
            print(f"   Expected: contains_sensitive_info=True, risk_level=high/critical")
            print(f"   Got: contains_sensitive_info={result.get('contains_sensitive_info')}, risk_level={result.get('risk_level')}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


def test_batch_analysis(client):
    """Test batch privacy analysis"""
    print("\n" + "=" * 80)
    print("TEST 6: Batch Privacy Analysis")
    print("=" * 80)
    
    test_texts = [
        {
            "text": "Meeting at 3 PM tomorrow.",
            "filename": "memo1.jpg"
        },
        {
            "text": "Password: MySecret123!",
            "filename": "sticky_note.jpg"
        },
        {
            "text": "Hello World!",
            "filename": "greeting.jpg"
        }
    ]
    
    try:
        results = client.batch_analyze_privacy(
            test_texts,
            progress_callback=lambda c, t, m: print(f"  Processing [{c}/{t}]: {m}")
        )
        
        print(f"\n✅ Batch analysis completed")
        print(f"Total analyzed: {len(results)}")
        
        # Generate summary
        summary = client.summarize_privacy_results(results)
        print(f"\nSummary:")
        print(f"  Total: {summary['total_analyzed']}")
        print(f"  Contains sensitive: {summary['contains_sensitive']}")
        print(f"  Risk levels: {summary['risk_levels']}")
        print(f"  Categories found: {summary['all_categories']}")
        
        if summary['high_risk_files']:
            print(f"\n  High-risk files detected:")
            for file in summary['high_risk_files']:
                print(f"    - {file['filename']}: {file['risk_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch analysis failed: {e}")
        return False


def test_error_handling(client):
    """Test error handling with malformed input"""
    print("\n" + "=" * 80)
    print("TEST 7: Error Handling")
    print("=" * 80)
    
    # Test with empty text
    try:
        result = client.analyze_privacy(text="", filename="empty.txt")
        print(f"✅ Handled empty text without crashing")
        print(f"   Result: {result.get('risk_level')}")
    except Exception as e:
        print(f"⚠️  Exception on empty text: {e}")
    
    # Test with very long text
    try:
        long_text = "Test " * 10000
        result = client.analyze_privacy(text=long_text, filename="long.txt")
        print(f"✅ Handled very long text without crashing")
    except Exception as e:
        print(f"⚠️  Exception on long text: {e}")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LLM PRIVACY ANALYSIS - TEST SUITE")
    print("=" * 80)
    print("\nThis script tests the LLM privacy analysis functionality")
    print("Make sure llama.cpp server is running before running tests\n")
    
    # Test 1: Connection
    client = test_llm_connection()
    if not client:
        print("\n❌ Cannot proceed without LLM server connection")
        return
    
    # Test 2: Simple query
    if not test_simple_query(client):
        print("\n❌ Basic query failed - check LLM server configuration")
        return
    
    # Test 3: JSON extraction
    test_json_extraction(client)
    
    # Test 4-7: Privacy analysis tests
    test_privacy_analysis_safe(client)
    test_privacy_analysis_sensitive(client)
    test_batch_analysis(client)
    test_error_handling(client)
    
    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETED")
    print("=" * 80)
    print("\nIf all tests passed, the LLM is ready for use in the pipeline!")
    print("You can now run: python ui.py")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
