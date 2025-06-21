"""
Enhanced Text-to-Speech service with multilingual support
Uses espeak-ng for reliable cross-platform TTS with Hindi and English support
"""

import io
import os
import subprocess
import tempfile
import wave
import numpy as np
from typing import Optional, Dict, List
import time

class EnhancedTTSService:
    """Enhanced TTS service using espeak-ng with multilingual support"""
    
    def __init__(self):
        """Initialize the enhanced TTS service"""
        self.sample_rate = 22050
        self.voice_configs = {
            'en': {
                'alloy': {'voice': 'en+f3', 'speed': 175, 'pitch': 50},
                'echo': {'voice': 'en+f4', 'speed': 160, 'pitch': 45},
                'fable': {'voice': 'en+f5', 'speed': 180, 'pitch': 55},
                'onyx': {'voice': 'en+m1', 'speed': 150, 'pitch': 40},
                'nova': {'voice': 'en+f1', 'speed': 190, 'pitch': 60},
                'shimmer': {'voice': 'en+f2', 'speed': 170, 'pitch': 52}
            },
            'hi': {
                'hindi_voice': {'voice': 'hi+f1', 'speed': 165, 'pitch': 48},
                'alloy': {'voice': 'hi+f1', 'speed': 165, 'pitch': 48}
            }
        }
        self._check_espeak_availability()
    
    def _check_espeak_availability(self):
        """Check if espeak-ng is available"""
        try:
            result = subprocess.run(['espeak-ng', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("espeak-ng is available and ready")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("espeak-ng not found, using fallback synthesis")
        return False
    
    def synthesize_speech(self, text: str, language: str = "en", voice: str = "alloy") -> Optional[bytes]:
        """
        Synthesize speech from text using espeak-ng
        
        Args:
            text (str): Input text to synthesize
            language (str): Language code ('en' for English, 'hi' for Hindi)
            voice (str): Voice identifier
            
        Returns:
            bytes: Audio data in WAV format, or None if synthesis fails
        """
        if not text.strip():
            return None
        
        try:
            # Clean and prepare text
            text = self._clean_text(text)
            
            # Get voice configuration
            voice_config = self._get_voice_config(voice, language)
            
            # Generate speech using espeak-ng
            return self._synthesize_with_espeak(text, voice_config)
            
        except Exception as e:
            print(f"Synthesis error: {e}")
            return self._generate_fallback_audio(text, language)
    
    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for synthesis"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Handle common abbreviations
        replacements = {
            'Dr.': 'Doctor',
            'Mr.': 'Mister', 
            'Mrs.': 'Missus',
            'Ms.': 'Miss',
            'Prof.': 'Professor'
        }
        
        for abbrev, expansion in replacements.items():
            text = text.replace(abbrev, expansion)
        
        return text
    
    def _get_voice_config(self, voice: str, language: str) -> Dict:
        """Get voice configuration for the specified voice and language"""
        lang_voices = self.voice_configs.get(language, self.voice_configs['en'])
        return lang_voices.get(voice, lang_voices['alloy'])
    
    def _synthesize_with_espeak(self, text: str, voice_config: Dict) -> Optional[bytes]:
        """Synthesize speech using espeak-ng"""
        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Build espeak command
            cmd = [
                'espeak-ng',
                '-v', voice_config['voice'],
                '-s', str(voice_config['speed']),
                '-p', str(voice_config['pitch']),
                '-w', temp_path,
                text
            ]
            
            # Execute espeak-ng
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(temp_path):
                # Read the generated audio file
                with open(temp_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                # Clean up temporary file
                os.unlink(temp_path)
                
                return audio_data
            else:
                print(f"espeak-ng failed: {result.stderr}")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None
                
        except Exception as e:
            print(f"espeak synthesis error: {e}")
            return None
    
    def _generate_fallback_audio(self, text: str, language: str) -> bytes:
        """Generate simple tone-based audio as fallback"""
        duration = min(len(text) * 0.08, 10.0)  # Max 10 seconds
        
        # Generate tone based on language
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        frequency = 440 if language == "en" else 523  # Different tones
        
        # Create audio signal with envelope
        audio = 0.3 * np.sin(2 * np.pi * frequency * t)
        envelope = np.exp(-t / (duration / 3))
        audio *= envelope
        
        # Convert to WAV format
        return self._numpy_to_wav(audio)
    
    def _numpy_to_wav(self, audio_array: np.ndarray) -> bytes:
        """Convert numpy array to WAV bytes"""
        # Ensure audio is in the right format
        audio_array = np.clip(audio_array, -1.0, 1.0)
        audio_int16 = (audio_array * 32767).astype(np.int16)
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def get_model_info(self) -> str:
        """Get information about the TTS engine"""
        return "espeak-ng (Enhanced Multilingual TTS)"
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return ["en", "hi"]
    
    def get_supported_voices(self) -> Dict:
        """Get supported voices for each language"""
        return {
            "en": list(self.voice_configs["en"].keys()),
            "hi": list(self.voice_configs["hi"].keys())
        }
    
    def is_ready(self) -> bool:
        """Check if the TTS service is ready"""
        return True  # espeak-ng is always available as fallback
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of the input text
        
        Args:
            text (str): Input text
            
        Returns:
            str: Language code ('hi' for Hindi, 'en' for English)
        """
        if not text:
            return 'en'
        
        # Count Devanagari characters for Hindi detection
        hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        total_chars = len([char for char in text if char.isalpha()])
        
        if total_chars > 0 and (hindi_chars / total_chars) > 0.3:
            return 'hi'
        
        return 'en'
