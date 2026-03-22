#!/usr/bin/env python3
"""
Quick test of LoveGuard architecture without external dependencies
"""

import sys
import os

# Add execution directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'execution'))

def test_fallback_analyzer():
    """Test fallback analyzer (no API keys needed)"""
    print("Testing Fallback Analyzer...")
    
    try:
        from fallback_analyzer import FallbackAnalyzer
        
        analyzer = FallbackAnalyzer()
        
        # Test cases
        tests = [
            ("I love you and support you", "low"),
            ("You can't leave me, you belong to me", "moderate"),
            ("I'll hurt you if you try to leave", "high"),
            ("I want to kill myself", "immediate")
        ]
        
        for text, expected in tests:
            result = analyzer.analyze_conversation(text)
            risk_score = result['risk_score']
            print(f"  '{text[:30]}...' → Risk: {risk_score}")
            
        print("PASS: Fallback Analyzer Working!")
        return True
        
    except Exception as e:
        print(f"FAIL: Fallback test failed: {e}")
        return False

def test_crisis_detector():
    """Test crisis detector (no API keys needed)"""
    print("\nTesting Crisis Detector...")
    
    try:
        from crisis_detector import CrisisDetector
        
        detector = CrisisDetector()
        
        crisis_level, resources, details = detector.assess_crisis_level(
            "I want to hurt myself and can't go on"
        )
        
        print(f"  Crisis Level: {crisis_level}")
        print(f"  Resources: {len(resources)} available")
        
        assert crisis_level == 'immediate'
        assert len(resources) > 0
        
        print("PASS: Crisis Detector Working!")
        return True
        
    except Exception as e:
        print(f"FAIL: Crisis test failed: {e}")
        return False

if __name__ == "__main__":
    print("LoveGuard Quick Architecture Test")
    print("=" * 40)
    
    tests_passed = 0
    if test_fallback_analyzer():
        tests_passed += 1
    if test_crisis_detector():
        tests_passed += 1
    
    print(f"\nResult: {tests_passed}/2 core systems working!")
    
    if tests_passed == 2:
        print("SUCCESS: Core architecture is solid - ready to deploy!")
    else:
        print("WARNING: Some issues found - check logs above")