"""
Independent Backend Server for TTS Application
Flask-based REST API with OpenAI compatibility
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import time
import io
import logging
from enhanced_tts_service import EnhancedTTSService
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global TTS service instance
tts_service = None

def initialize_tts():
    """Initialize TTS service"""
    global tts_service
    if tts_service is None:
        tts_service = EnhancedTTSService()
    return tts_service

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "TTS API Backend",
        "timestamp": time.time(),
        "version": "1.0.0"
    })

@app.route('/v1/audio/speech', methods=['POST'])
def create_speech():
    """
    OpenAI-compatible TTS endpoint
    
    Expected request body:
    {
        "model": "tts-1",
        "input": "The text to synthesize",
        "voice": "alloy",
        "response_format": "wav"
    }
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract parameters
        text = data.get('input', '')
        model = data.get('model', 'tts-1')
        voice = data.get('voice', 'alloy')
        response_format = data.get('response_format', 'wav')
        speed = data.get('speed', 1.0)
        
        # Validate input
        if not text.strip():
            return jsonify({"error": "Input text is required"}), 400
        
        # Detect language
        language = detect_language(text)
        
        logger.info(f"Synthesizing text: '{text[:50]}...' in language: {language}")
        
        # Initialize TTS service if needed
        tts = initialize_tts()
        
        # Generate speech
        audio_data = tts.synthesize_speech(text, language, voice)
        
        if audio_data is None:
            return jsonify({"error": "Failed to generate speech"}), 500
        
        # Determine content type based on format
        content_type = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'opus': 'audio/opus',
            'aac': 'audio/aac',
            'flac': 'audio/flac'
        }.get(response_format, 'audio/wav')
        
        # Return audio as streaming response
        return Response(
            audio_data,
            mimetype=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="speech.{response_format}"',
                'Content-Length': str(len(audio_data)),
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        logger.error(f"Error in create_speech: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    """List available TTS models (OpenAI-compatible)"""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "tts-1",
                "object": "model",
                "created": 1677610602,
                "owned_by": "enhanced-tts"
            },
            {
                "id": "tts-1-hd",
                "object": "model", 
                "created": 1677610602,
                "owned_by": "enhanced-tts"
            }
        ]
    })

@app.route('/v1/voices', methods=['GET'])
def list_voices():
    """List available voices"""
    tts = initialize_tts()
    voices = tts.get_supported_voices()
    
    voice_list = []
    for lang, voice_names in voices.items():
        for voice_name in voice_names:
            voice_list.append({
                "id": voice_name,
                "name": voice_name.title(),
                "language": lang,
                "description": f"Voice for {lang.upper()} language"
            })
    
    return jsonify({"voices": voice_list})

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get supported languages"""
    tts = initialize_tts()
    return jsonify({
        "languages": tts.get_supported_languages(),
        "default": "en"
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get service status and capabilities"""
    tts = initialize_tts()
    return jsonify({
        "status": "ready" if tts.is_ready() else "not_ready",
        "engine": tts.get_model_info(),
        "supported_languages": tts.get_supported_languages(),
        "supported_voices": tts.get_supported_voices(),
        "capabilities": {
            "streaming": True,
            "multiple_voices": True,
            "language_detection": True,
            "openai_compatible": True
        }
    })

def detect_language(text: str) -> str:
    """
    Simple language detection for Hindi vs English
    
    Args:
        text (str): Input text
        
    Returns:
        str: Language code ('hi' for Hindi, 'en' for English)
    """
    # Check for Devanagari script (Hindi)
    hindi_chars = 0
    total_chars = 0
    
    for char in text:
        if char.isalpha():
            total_chars += 1
            # Check if character is in Devanagari range
            if '\u0900' <= char <= '\u097F':
                hindi_chars += 1
    
    # If more than 30% of alphabetic characters are Devanagari, consider it Hindi
    if total_chars > 0 and (hindi_chars / total_chars) > 0.3:
        return 'hi'
    
    return 'en'

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({"error": "Method not allowed"}), 405




if __name__ == "__main__":
    logger.info("Starting TTS Backend Server...")
    initialize_tts()
    port = int(os.environ.get("PORT", 8000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        threaded=True
    )
