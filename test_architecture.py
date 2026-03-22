#!/usr/bin/env python3
"""
Test script for LoveGuard 3-layer architecture
Validates that all components work together correctly
"""

import sys
import os
import json

# Add current directory to Python path
sys.path.append(os.path.dirname(__file__))

from app_orchestrator import LoveGuardOrchestrator

def test_conversation_analysis():
    """Test conversation analysis workflow"""
    print("🧪 Testing Conversation Analysis...")
    
    try:
        orchestrator = LoveGuardOrchestrator()
        
        # Test cases
        test_cases = [
            {
                'name': 'Healthy conversation',
                'text': 'I love you and I support your decisions. What do you think about this?',
                'expected_risk': 'low'
            },
            {
                'name': 'Controlling behavior',
                'text': 'You can\'t go out with your friends. I forbid you from seeing them.',
                'expected_risk': 'moderate'
            },
            {
                'name': 'Threatening language',
                'text': 'I\'ll hurt you if you leave me. You belong to me.',
                'expected_risk': 'high'
            },
            {
                'name': 'Crisis language',
                'text': 'I want to kill myself. I can\'t go on anymore.',
                'expected_risk': 'immediate'
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            
            result = orchestrator.analyze_conversation(
                conversation_text=test_case['text'],
                include_context=True,
                detailed=False,
                user_tier='free'
            )
            
            risk_score = result['risk_score']
            crisis_level = result['crisis_level']
            analysis_method = result['analysis_method']
            
            print(f"    Risk Score: {risk_score}")
            print(f"    Crisis Level: {crisis_level}")
            print(f"    Analysis Method: {analysis_method}")
            print(f"    Red Flags: {len(result.get('red_flags', []))}")
            
            # Basic validation
            assert isinstance(risk_score, (int, float)), "Risk score must be numeric"
            assert 0 <= risk_score <= 100, "Risk score must be 0-100"
            assert crisis_level in ['immediate', 'high', 'moderate', 'low'], "Invalid crisis level"
            
            print(f"    ✅ Passed")
        
        print("\n✅ Conversation Analysis Tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Conversation Analysis Tests FAILED: {e}")
        return False

def test_payment_processing():
    """Test payment processing workflow"""
    print("\n🧪 Testing Payment Processing...")
    
    try:
        orchestrator = LoveGuardOrchestrator()
        
        # Test payment initiation (will fail without real API keys, which is expected)
        result = orchestrator.process_payment(
            user_email="test@example.com",
            payment_type="monthly_subscription"
        )
        
        print(f"  Payment Result: {result.get('payment_status', 'unknown')}")
        
        # Should either work or fail gracefully
        assert 'payment_status' in result, "Payment result must include status"
        
        # Test subscription status
        status = orchestrator.get_user_subscription_status("test@example.com")
        print(f"  Subscription Status: {status.get('tier', 'unknown')}")
        
        print("✅ Payment Processing Tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Payment Processing Tests FAILED: {e}")
        return False

def test_error_handling():
    """Test error handling and self-annealing"""
    print("\n🧪 Testing Error Handling...")
    
    try:
        orchestrator = LoveGuardOrchestrator()
        
        # Test empty conversation
        try:
            orchestrator.analyze_conversation("")
            assert False, "Should have failed with empty text"
        except ValueError:
            print("  ✅ Empty text validation works")
        
        # Test error handling
        fake_error = Exception("Test error for annealing")
        error_result = orchestrator.handle_error_and_self_anneal("test_operation", fake_error)
        
        assert error_result['success'] == False, "Error result should indicate failure"
        assert 'error' in error_result, "Error result should contain error message"
        
        print("  ✅ Error handling works")
        
        # Test system status
        status = orchestrator.get_system_status()
        print(f"  System Status: {json.dumps(status, indent=2)}")
        
        assert isinstance(status['system_healthy'], bool), "System health should be boolean"
        
        print("✅ Error Handling Tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error Handling Tests FAILED: {e}")
        return False

def test_fallback_system():
    """Test fallback analysis system"""
    print("\n🧪 Testing Fallback System...")
    
    try:
        # Import fallback analyzer directly
        from execution.fallback_analyzer import FallbackAnalyzer
        
        analyzer = FallbackAnalyzer()
        
        result = analyzer.analyze_conversation(
            "You're worthless and nobody will love you",
            detailed=True
        )
        
        print(f"  Fallback Risk Score: {result['risk_score']}")
        print(f"  Analysis Method: {result['analysis_method']}")
        
        assert result['analysis_method'] == 'fallback', "Should use fallback method"
        assert result['risk_score'] > 0, "Should detect concerning language"
        
        print("✅ Fallback System Tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Fallback System Tests FAILED: {e}")
        return False

def test_crisis_detection():
    """Test crisis detection system"""
    print("\n🧪 Testing Crisis Detection...")
    
    try:
        from execution.crisis_detector import CrisisDetector
        
        detector = CrisisDetector()
        
        # Test immediate crisis
        crisis_level, resources, details = detector.assess_crisis_level(
            "I want to kill myself tonight"
        )
        
        print(f"  Crisis Level: {crisis_level}")
        print(f"  Resources Count: {len(resources)}")
        
        assert crisis_level == 'immediate', "Should detect immediate crisis"
        assert len(resources) > 0, "Should provide safety resources"
        
        # Test safety plan generation
        safety_plan = detector.generate_safety_plan(crisis_level)
        print(f"  Safety Plan Steps: {len(safety_plan)}")
        
        assert len(safety_plan) > 0, "Should generate safety plan"
        
        print("✅ Crisis Detection Tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Crisis Detection Tests FAILED: {e}")
        return False

def main():
    """Run all architecture tests"""
    print("🚀 LoveGuard 3-Layer Architecture Test Suite")
    print("=" * 50)
    
    tests = [
        test_conversation_analysis,
        test_payment_processing,
        test_error_handling,
        test_fallback_system,
        test_crisis_detection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Architecture is working correctly.")
        return True
    else:
        print("⚠️ Some tests FAILED. Check configuration and dependencies.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)