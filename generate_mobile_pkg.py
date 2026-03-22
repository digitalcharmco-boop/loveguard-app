import os
import textwrap

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print(f"Created: {path}")

def generate_mobile_app():
    base_dir = "loveguard_mobile"
    
    # 1. pubspec.yaml
    pubspec_content = """
name: loveguard
description: AI-Powered Relationship Safety Mobile App
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2
  google_fonts: ^5.1.0
  supabase_flutter: ^1.10.0
  http: ^1.1.0
  provider: ^6.0.5
  intl: ^0.18.1
  url_launcher: ^6.1.11

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
"""
    create_file(f"{base_dir}/pubspec.yaml", pubspec_content)
    
    # 2. lib/main.dart
    main_dart = """
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'screens/welcome_page.dart';
import 'theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Supabase
  // TODO: Replace with your actual Supabase URL and Anon Key
  await Supabase.initialize(
    url: 'YOUR_SUPABASE_URL',
    anonKey: 'YOUR_SUPABASE_ANON_KEY',
  );

  runApp(const LoveGuardApp());
}

class LoveGuardApp extends StatelessWidget {
  const LoveGuardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LoveGuard',
      theme: LoveGuardTheme.themeData,
      home: const WelcomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}
"""
    create_file(f"{base_dir}/lib/main.dart", main_dart)
    
    # 3. lib/theme.dart
    theme_dart = """
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class LoveGuardTheme {
  static const Color primaryColor = Color(0xFFFF6B6B);
  static const Color secondaryColor = Color(0xFF4ECDC4);
  static const Color tertiaryColor = Color(0xFFFFE66D);
  static const Color backgroundColor = Color(0xFFF7F9FC);
  static const Color textColor = Color(0xFF2C3E50);
  static const Color errorColor = Color(0xFFE74C3C);
  static const Color successColor = Color(0xFF2ECC71);

  static ThemeData get themeData {
    return ThemeData(
      primaryColor: primaryColor,
      scaffoldBackgroundColor: backgroundColor,
      textTheme: TextTheme(
        displayLarge: GoogleFonts.poppins(
          fontSize: 32,
          fontWeight: FontWeight.bold,
          color: textColor,
        ),
        displayMedium: GoogleFonts.poppins(
          fontSize: 24,
          fontWeight: FontWeight.bold,
          color: textColor,
        ),
        bodyLarge: GoogleFonts.openSans(
          fontSize: 16,
          color: textColor,
        ),
        labelLarge: GoogleFonts.poppins(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryColor,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          textStyle: GoogleFonts.poppins(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Colors.transparent),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: primaryColor),
        ),
        contentPadding: const EdgeInsets.all(16),
      ),
    );
  }
}
"""
    create_file(f"{base_dir}/lib/theme.dart", theme_dart)

    # 4. lib/screens/welcome_page.dart
    welcome_dart = """
import 'package:flutter/material.dart';
import 'package:loveguard/theme.dart';
// import 'login_page.dart';  // Future implementation
// import 'signup_page.dart'; // Future implementation

class WelcomePage extends StatelessWidget {
  const WelcomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // Hero Section
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(32, 64, 32, 48),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  LoveGuardTheme.primaryColor,
                  LoveGuardTheme.secondaryColor,
                ],
              ),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(40),
                bottomRight: Radius.circular(40),
              ),
            ),
            child: Column(
              children: [
                const Icon(
                  Icons.favorite,
                  size: 80,
                  color: Colors.white,
                ),
                const SizedBox(height: 24),
                Text(
                  "LoveGuard",
                  style: Theme.of(context).textTheme.displayLarge?.copyWith(
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  "AI-Powered Relationship Insights",
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 18,
                  ),
                ),
              ],
            ),
          ),
          
          // Value Proposition
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Text(
                    "Understand Your Relationship Patterns",
                    style: Theme.of(context).textTheme.displayMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),
                  _buildFeatureRow(context, "AI conversation analysis"),
                  _buildFeatureRow(context, "Spot concerning patterns"),
                  _buildFeatureRow(context, "Educational insights"),
                  _buildFeatureRow(context, "Safety resources included"),
                ],
              ),
            ),
          ),
          
          // CTA Section
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      // Navigate to Signup
                    },
                    child: const Text("Get Started"),
                  ),
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () {
                    // Navigate to Login
                  },
                  child: Text(
                    "Already have an account? Sign In",
                    style: TextStyle(color: LoveGuardTheme.primaryColor),
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  "For educational purposes • Ages 18+ only",
                  style: Theme.of(context).textTheme.bodySmall,
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureRow(BuildContext context, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          const Icon(
            Icons.check_circle,
            color: LoveGuardTheme.successColor,
            size: 24,
          ),
          const SizedBox(width: 12),
          Text(
            text,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ],
      ),
    );
  }
}
"""
    create_file(f"{base_dir}/lib/screens/welcome_page.dart", welcome_dart)

    # 5. lib/services/api_service.dart
    api_service_dart = """
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // TODO: Secure this key properly in production (e.g., backend proxy or env vars)
  static const String _openAIKey = 'YOUR_OPENAI_KEY';
  
  static Future<Map<String, dynamic>> analyzeConversationAdvanced(String conversationText) async {
    if (conversationText.trim().isEmpty) {
      return {'error': 'Please enter a conversation to analyze.', 'risk_score': 0};
    }

    if (conversationText.trim().length < 20) {
      return {'error': 'Please enter a longer conversation for accurate analysis.', 'risk_score': 0};
    }

    // Crisis keywords for immediate local detection
    final List<String> crisisKeywords = [
      'hurt me', 'hit me', 'kill me', 'murder', 'weapon', 'gun', 'knife',
      'threatened to', 'going to hurt', 'won\\'t let me leave', 'trapped',
      'stalking', 'following me', 'scared for my life'
    ];

    bool crisisDetected = crisisKeywords.any(
      (keyword) => conversationText.toLowerCase().contains(keyword)
    );

    final analysisPrompt = '''
  You are LoveGuard AI, a relationship safety expert. Analyze this conversation for manipulation tactics and concerning patterns.
  
  CONVERSATION: "$conversationText"
  
  Provide analysis in this EXACT JSON format:
  {
    "risk_score": [number 1-100],
    "risk_level": "[LOW/MODERATE/HIGH]",
    "red_flags": [{"type": "string", "description": "string", "severity": "LOW/MEDIUM/HIGH"}],
    "explanation": "string",
    "recommendations": ["string"],
    "educational_insight": "string",
    "crisis_indicators": ${crisisDetected ? 'true' : 'false'}
  }
  ''';

    try {
      final response = await http.post(
        Uri.parse('https://api.openai.com/v1/chat/completions'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_openAIKey',
        },
        body: jsonEncode({
          'model': 'gpt-4',
          'messages': [
            {'role': 'system', 'content': 'You are a relationship safety expert. Return valid JSON only.'},
            {'role': 'user', 'content': analysisPrompt}
          ],
          'max_tokens': 1500,
          'temperature': 0.1,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final content = data['choices'][0]['message']['content'];
        try {
          final result = jsonDecode(content);
          result['crisis_indicators'] = crisisDetected || (result['crisis_indicators'] ?? false);
          
          if (crisisDetected && (result['risk_score'] ?? 0) < 85) {
             result['risk_score'] = 85;
             result['risk_level'] = 'HIGH';
          }
          return result;
        } catch (e) {
          return {
            'risk_score': crisisDetected ? 85 : 50,
            'risk_level': crisisDetected ? 'HIGH' : 'MODERATE',
            'error': 'JSON Parse Error',
            'explanation': 'Analyzed with local fallback due to processed error.'
          };
        }
      } else {
        return {'error': 'Service unavailable', 'risk_score': 0};
      }
    } catch (e) {
      return {'error': 'Network error', 'risk_score': 0};
    }
  }
}
"""
    create_file(f"{base_dir}/lib/services/api_service.dart", api_service_dart)

    # 6. lib/screens/home_page.dart
    home_page_dart = """
import 'package:flutter/material.dart';
import 'package:loveguard/theme.dart';
import 'package:loveguard/services/api_service.dart';
import 'results_page.dart';  // We will create this next

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final TextEditingController _controller = TextEditingController();
  bool _isLoading = false;

  void _analyze() async {
    setState(() => _isLoading = true);
    
    // Simulate or call real API
    final result = await ApiService.analyzeConversationAdvanced(_controller.text);
    
    if (mounted) {
      setState(() => _isLoading = false);
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ResultsPage(result: result),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("LoveGuard Analysis"),
        backgroundColor: LoveGuardTheme.primaryColor,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              "How is your relationship feeling today?",
              style: Theme.of(context).textTheme.displayMedium?.copyWith(fontSize: 24),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _controller,
              maxLines: 8,
              decoration: const InputDecoration(
                hintText: "Paste text messages or conversation here...",
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isLoading ? null : _analyze,
              child: _isLoading 
                ? const CircularProgressIndicator(color: Colors.white)
                : const Text("Analyze Conversation"),
            ),
          ],
        ),
      ),
    );
  }
}
"""
    create_file(f"{base_dir}/lib/screens/home_page.dart", home_page_dart)

    # 7. lib/screens/results_page.dart
    results_page_dart = """
import 'package:flutter/material.dart';
import 'package:loveguard/theme.dart';
import 'package:url_launcher/url_launcher.dart';

class ResultsPage extends StatelessWidget {
  final Map<String, dynamic> result;

  const ResultsPage({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final int riskScore = result['risk_score'] ?? 0;
    final String riskLevel = result['risk_level'] ?? 'UNKNOWN';
    final List redFlags = result['red_flags'] ?? [];
    final bool crisis = result['crisis_indicators'] ?? false;

    Color riskColor = LoveGuardTheme.successColor;
    if (riskScore > 30) riskColor = LoveGuardTheme.tertiaryColor;
    if (riskScore > 70) riskColor = LoveGuardTheme.errorColor;

    return Scaffold(
      appBar: AppBar(title: const Text("Analysis Results")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Risk Score
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: riskColor, width: 2),
              ),
              child: Column(
                children: [
                  Text(
                    "$riskScore/100",
                    style: Theme.of(context).textTheme.displayLarge?.copyWith(color: riskColor),
                  ),
                  Text("Risk: $riskLevel", style: Theme.of(context).textTheme.headlineSmall),
                ],
              ),
            ),
            const SizedBox(height: 20),
            
            // Crisis Alert
            if (crisis || riskScore > 80)
              Container(
                margin: const EdgeInsets.only(bottom: 20),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: LoveGuardTheme.errorColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  children: [
                    const Text(
                      "⚠️ Safety Concern Detected",
                      style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 10),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.red),
                      onPressed: () => launchUrl(Uri.parse("tel:911")),
                      child: const Text("Call Emergency Services"),
                    ),
                  ],
                ),
              ),

            // Explanation
            if (result['explanation'] != null)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                child: Text(result['explanation']),
              ),

            // Red Flags
             const SizedBox(height: 20),
             if (redFlags.isNotEmpty) ...[
               const Align(alignment: Alignment.centerLeft, child: Text("🚩 Red Flags", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold))),
               const SizedBox(height: 10),
               ...redFlags.map((flag) => Card(
                 child: ListTile(
                   leading: const Icon(Icons.flag, color: Colors.orange),
                   title: Text(flag['type'] ?? 'Concern'),
                   subtitle: Text(flag['description'] ?? ''),
                 ),
               )),
             ],
          ],
        ),
      ),
    );
  }
}
"""
    create_file(f"{base_dir}/lib/screens/results_page.dart", results_page_dart)

    # Update main.dart to link to HomePage for dev purposes (skipping auth for demo if needed)
    # But for now, we leave main.dart pointing to WelcomePage as generated before.

    print("Mobile app structure generated successfully in 'loveguard_mobile/'")
    print("Run 'python generate_mobile_pkg.py' to execute this generation.")

if __name__ == "__main__":
    generate_mobile_app()
