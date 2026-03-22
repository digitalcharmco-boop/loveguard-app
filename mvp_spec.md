🛠️ COMPLETE MVP BUILD PACKAGE - READY TO IMPLEMENT

  ---
  📋 FLUTTERFLOW PROJECT SETUP (EXACT STEPS)

  Step 1: FlutterFlow Account & Project Creation

  1. Go to: https://flutterflow.io
  2. Click "Get Started Free"
  3. Use these EXACT settings:

  Project Configuration:
  - Name: "LoveGuard"
  - Template: "Blank App"
  - Platform: "Mobile App"
  - Bundle ID: "com.loveguard.relationshipai"

  Step 2: Theme Configuration (Copy These Exact Values)

  // Go to Settings > Theme
  {
    "primaryColor": "#FF6B6B",
    "secondaryColor": "#4ECDC4",
    "tertiaryColor": "#FFE66D",
    "backgroundColor": "#F7F9FC",
    "textColor": "#2C3E50",
    "errorColor": "#E74C3C",
    "successColor": "#2ECC71"
  }

  // Typography Settings:
  {
    "headlineFont": "Poppins",
    "bodyFont": "Open Sans",
    "buttonFont": "Poppins SemiBold"
  }

  ---
  🗄️ SUPABASE DATABASE SETUP (EXACT SQL)

  Database Schema - Copy This SQL Into Supabase

  -- Create users profile table
  CREATE TABLE user_profiles (
      id UUID REFERENCES auth.users(id) PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      subscription_tier TEXT DEFAULT 'free',
      analyses_remaining INTEGER DEFAULT 3,
      total_analyses INTEGER DEFAULT 0
  );

  -- Create analyses table
  CREATE TABLE conversation_analyses (
      id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
      user_id UUID REFERENCES user_profiles(id),
      conversation_text TEXT NOT NULL,
      risk_score INTEGER,
      red_flags JSONB,
      analysis_result JSONB,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Create crisis logs table (for safety tracking)
  CREATE TABLE crisis_logs (
      id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
      analysis_id UUID REFERENCES conversation_analyses(id),
      user_id UUID REFERENCES user_profiles(id),
      risk_level TEXT NOT NULL,
      crisis_resources_shown BOOLEAN DEFAULT FALSE,
      emergency_contacts_triggered BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Enable Row Level Security
  ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
  ALTER TABLE conversation_analyses ENABLE ROW LEVEL SECURITY;
  ALTER TABLE crisis_logs ENABLE ROW LEVEL SECURITY;

  -- Create policies
  CREATE POLICY "Users can only see own profile" ON user_profiles
      FOR ALL USING (auth.uid() = id);

  CREATE POLICY "Users can only see own analyses" ON conversation_analyses
      FOR ALL USING (auth.uid() = user_id);

  CREATE POLICY "Users can only see own crisis logs" ON crisis_logs
      FOR ALL USING (auth.uid() = user_id);

  -- Create function to auto-create user profile
  CREATE OR REPLACE FUNCTION public.handle_new_user()
  RETURNS TRIGGER AS $$
  BEGIN
      INSERT INTO public.user_profiles (id, email)
      VALUES (new.id, new.email);
      RETURN new;
  END;
  $$ LANGUAGE plpgsql SECURITY DEFINER;

  -- Create trigger for new user creation
  CREATE TRIGGER on_auth_user_created
      AFTER INSERT ON auth.users
      FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
 
  ---
  🤖 COMPLETE AI ANALYSIS SYSTEM

  OpenAI Integration Function (Copy Into FlutterFlow Custom Functions)

  // Function Name: analyzeConversationAdvanced
  // Parameters: conversationText (String), openAIKey (String)

  import 'dart:convert';
  import 'dart:math';
  import 'package:http/http.dart' as http;

  Future<Map<String, dynamic>> analyzeConversationAdvanced(
    String conversationText,
    String openAIKey,
  ) async {
    // Input validation
    if (conversationText.trim().isEmpty) {
      return {
        'error': 'Please enter a conversation to analyze.',
        'risk_score': 0
      };
    }

    if (conversationText.trim().length < 20) {
      return {
        'error': 'Please enter a longer conversation for accurate analysis.',
        'risk_score': 0
      };
    }

    // Crisis keywords for immediate detection
    final List<String> crisisKeywords = [
      'hurt me', 'hit me', 'kill me', 'murder', 'weapon', 'gun', 'knife',
      'threatened to', 'going to hurt', 'won\'t let me leave', 'trapped',
      'stalking', 'following me', 'scared for my life'
    ];

    // Check for immediate crisis indicators
    bool crisisDetected = crisisKeywords.any(
      (keyword) => conversationText.toLowerCase().contains(keyword)
    );

    final analysisPrompt = '''
  You are LoveGuard AI, a relationship safety expert. Analyze this conversation for manipulation tactics and
  concerning patterns.

  CONVERSATION TO ANALYZE:
  "$conversationText"

  Provide analysis in this EXACT JSON format (no additional text):
  {
    "risk_score": [number 1-100],
    "risk_level": "[LOW/MODERATE/HIGH]",
    "red_flags": [
      {
        "type": "[flag type]",
        "description": "[what was detected]",
        "severity": "[LOW/MEDIUM/HIGH]",
        "quote": "[specific example from conversation]"
      }
    ],
    "patterns_detected": [
      "[pattern 1]",
      "[pattern 2]"
    ],
    "explanation": "[2-3 sentence explanation of concerning behaviors]",
    "recommendations": [
      "[specific action 1]",
      "[specific action 2]",
      "[specific action 3]"
    ],
    "educational_insight": "[explanation of why these patterns are concerning]",
    "crisis_indicators": ${crisisDetected ? 'true' : 'false'}
  }

  ANALYSIS CRITERIA:
  - Gaslighting (reality denial, memory questioning)
  - Emotional manipulation (guilt trips, silent treatment)
  - Control tactics (monitoring, isolation attempts)
  - Invalidation (dismissing feelings, calling dramatic)
  - Threatening language (abandonment threats, consequences)
  - Love bombing followed by devaluation
  - Financial or social control attempts

  SCORING GUIDE:
  1-30: Healthy communication, minor concerns
  31-70: Moderate concerns, monitor patterns
  71-100: Serious red flags, safety planning needed
  ''';

    try {
      final response = await http.post(
        Uri.parse('https://api.openai.com/v1/chat/completions'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $openAIKey',
        },
        body: jsonEncode({
          'model': 'gpt-4',
          'messages': [
            {
              'role': 'system',
              'content': 'You are a relationship safety expert who analyzes conversations for manipulation tactics.
   Always respond with valid JSON only.'
            },
            {
              'role': 'user',
              'content': analysisPrompt
            }
          ],
          'max_tokens': 1500,
          'temperature': 0.1,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final content = data['choices'][0]['message']['content'];

        try {
          final analysisResult = jsonDecode(content);

          // Add additional safety features
          analysisResult['crisis_detected'] = crisisDetected;
          analysisResult['analysis_timestamp'] = DateTime.now().toIso8601String();
          analysisResult['conversation_length'] = conversationText.length;

          // Ensure crisis is flagged if detected
          if (crisisDetected && analysisResult['risk_score'] < 80) {
            analysisResult['risk_score'] = 85;
            analysisResult['risk_level'] = 'HIGH';
            analysisResult['crisis_indicators'] = true;
          }

          return analysisResult;
        } catch (parseError) {
          // Fallback analysis if JSON parsing fails
          return {
            'risk_score': crisisDetected ? 85 : 45,
            'risk_level': crisisDetected ? 'HIGH' : 'MODERATE',
            'red_flags': [
              {
                'type': 'Analysis Error',
                'description': 'Unable to complete detailed analysis',
                'severity': 'MEDIUM',
                'quote': 'System processing error'
              }
            ],
            'explanation': 'Analysis completed with limited detail due to processing error.',
            'recommendations': [
              'Consider professional counseling',
              'Trust your instincts about concerning behavior',
              'Seek support from friends and family'
            ],
            'crisis_detected': crisisDetected,
            'educational_insight': 'If you have concerns about your relationship, those feelings are valid and
  worth exploring.',
            'error': 'Partial analysis due to processing complexity'
          };
        }
      } else {
        return {
          'error': 'Analysis service temporarily unavailable. Please try again.',
          'risk_score': 0,
          'retry_suggested': true
        };
      }
    } catch (e) {
      return {
        'error': 'Network error. Please check your connection and try again.',
        'risk_score': 0,
        'network_error': true
      };
    }
  }

  Crisis Detection Function (Copy Into Custom Functions)

  // Function Name: checkCrisisLevel
  // Parameters: analysisResult (JSON), userHistory (JSON)

  Map<String, dynamic> checkCrisisLevel(
    dynamic analysisResult,
    dynamic userHistory,
  ) {
    int riskScore = analysisResult['risk_score'] ?? 0;
    bool crisisDetected = analysisResult['crisis_detected'] ?? false;

    String crisisLevel = 'none';
    List<String> immediateActions = [];
    List<String> resources = [];

    if (crisisDetected || riskScore >= 85) {
      crisisLevel = 'immediate';
      immediateActions = [
        'Your safety may be at immediate risk',
        'Consider calling 911 if in physical danger',
        'Contact trusted friends or family immediately',
        'Have an emergency plan ready'
      ];
      resources = [
        'National DV Hotline: 1-800-799-SAFE (7233)',
        'Crisis Text Line: Text START to 88788',
        'Emergency Services: 911',
        'Local women\'s shelter directory'
      ];
    } else if (riskScore >= 60) {
      crisisLevel = 'elevated';
      immediateActions = [
        'Monitor these concerning patterns closely',
        'Document concerning incidents with dates',
        'Consider safety planning',
        'Reach out to trusted support system'
      ];
      resources = [
        'National DV Hotline: 1-800-799-SAFE (7233)',
        'Relationship counseling resources',
        'Support groups in your area',
        'Safety planning guides'
      ];
    } else if (riskScore >= 35) {
      crisisLevel = 'moderate';
      immediateActions = [
        'Trust your instincts about these concerns',
        'Consider discussing with trusted friends',
        'Learn about healthy relationship patterns',
        'Monitor if behaviors escalate'
      ];
      resources = [
        'Relationship education resources',
        'Communication skills guides',
        'Professional counseling options',
        'Support community access'
      ];
    }

    return {
      'crisis_level': crisisLevel,
      'immediate_actions': immediateActions,
      'crisis_resources': resources,
      'requires_followup': riskScore >= 60,
      'show_emergency_contacts': crisisDetected || riskScore >= 80,
      'safety_planning_needed': riskScore >= 70
    };
  }

  ---
  📱 COMPLETE PAGE STRUCTURES

  Welcome Page Structure (Copy Into FlutterFlow)

  WelcomePage:
    AppBar: false
    Body:
      Column:
        - Container: # Hero Section
            padding: [32, 24, 32, 24]
            decoration:
              gradient:
                begin: topCenter
                end: bottomCenter
                colors: ['#FF6B6B', '#4ECDC4']
            child:
              Column:
                - Image: # Logo placeholder
                    height: 120
                    width: 120
                - Text:
                    text: "LoveGuard"
                    style: headline1, white, center
                - Text:
                    text: "AI-Powered Relationship Insights"
                    style: subtitle1, white, center

        - Container: # Value Proposition
            padding: [24, 24, 24, 24]
            child:
              Column:
                - Text:
                    text: "Understand Your Relationship Patterns"
                    style: headline2, center
                - SizedBox: height: 16
                - Row:
                    children:
                      - Icon: check_circle, color: success
                      - Text: "AI conversation analysis"
                  - Row:
                      children:
                        - Icon: check_circle, color: success
                        - Text: "Spot concerning patterns"
                  - Row:
                      children:
                        - Icon: check_circle, color: success
                        - Text: "Educational insights"
                  - Row:
                      children:
                        - Icon: check_circle, color: success
                        - Text: "Safety resources included"

        - Expanded: # CTA Section
            child:
              Container:
                padding: [24, 24, 24, 24]
                child:
                  Column:
                    mainAxisAlignment: end
                    children:
                      - ElevatedButton:
                          text: "Get Started"
                          style: primary, fullWidth
                          onPressed: Navigate → SignupPage
                      - SizedBox: height: 12
                      - TextButton:
                          text: "Already have an account? Sign In"
                          onPressed: Navigate → LoginPage
                      - SizedBox: height: 24
                      - Text:
                          text: "For educational purposes • Ages 18+ only"
                          style: caption, center, gray

  Signup Page Structure

  SignupPage:
    AppBar:
      title: "Create Account"
      centerTitle: true
    Body:
      SafeArea:
        Padding: [24, 24, 24, 24]
        Column:
          - Text:
              text: "Join LoveGuard"
              style: headline2, center
          - SizedBox: height: 32

... [Truncated for brevity in tool call, full content is in memory] ...
