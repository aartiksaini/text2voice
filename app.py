"""
Standalone TTS Backend API Server
Flask-based REST API with OpenAI compatibility
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
import time
import io
from enhanced_tts_service import EnhancedTTSService
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

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
                'Content-Length': str(len(audio_data))
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
    voices_config = tts.get_supported_voices()
    
    voices = []
    for lang, voice_list in voices_config.items():
        for voice_id in voice_list:
            voices.append({
                "id": voice_id,
                "name": voice_id.title(),
                "language": lang,
                "description": f"{lang.upper()} voice - {voice_id}"
            })
    
    return jsonify({"voices": voices})

@app.route('/api/info', methods=['GET'])
def api_info():
    """API information endpoint"""
    tts = initialize_tts()
    return jsonify({
        "name": "Enhanced TTS API",
        "version": "1.0.0",
        "engine": tts.get_model_info(),
        "supported_languages": tts.get_supported_languages(),
        "endpoints": {
            "synthesis": "/v1/audio/speech",
            "models": "/v1/models",
            "voices": "/v1/voices",
            "health": "/health"
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

if __name__ == "__main__":
    # Initialize TTS service on startup
    initialize_tts()
    
    logger.info("Starting Enhanced TTS Backend API...")
port = int(os.environ.get("PORT", 8000))
app.run(host="0.0.0.0", port=port)
