"""
Text-to-Speech module for the chatbot application.
This module provides functionality to convert text responses from the chatbot
to speech using pyttsx3 or other TTS libraries.
"""
import pyttsx3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import tempfile
import os
import uvicorn
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TTS_Service")

app = FastAPI(title="Text-to-Speech Service",
              description="Service for converting text to speech for the chatbot UI")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech conversion"""
    text: str
    voice_id: str = "default"  # Default voice ID
    rate: int = 200  # Speaking rate (words per minute)

@app.post("/tts")
async def convert_text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech and return an audio file
    
    Args:
        request: TextToSpeechRequest object containing the text to convert
        
    Returns:
        FileResponse: Audio file with the synthesized speech
    """
    try:
        engine = pyttsx3.init()
        
        # Configure voice properties
        engine.setProperty('rate', request.rate)
        
        # Get available voices
        voices = engine.getProperty('voices')
        
        # Set voice if specified and available
        if request.voice_id != "default" and len(voices) > 0:
            try:
                voice_index = int(request.voice_id)
                if 0 <= voice_index < len(voices):
                    engine.setProperty('voice', voices[voice_index].id)
            except ValueError:
                # If voice_id is not an integer index, try to match by ID
                for voice in voices:
                    if request.voice_id in voice.id:
                        engine.setProperty('voice', voice.id)
                        break
        
        # Create a temporary file for the audio output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_filename = temp_audio.name
        
        # Generate speech and save to file
        engine.save_to_file(request.text, temp_filename)
        engine.runAndWait()
        
        logger.info(f"Generated speech audio saved to {temp_filename}")
        
        # Return the audio file
        return FileResponse(
            path=temp_filename,
            media_type="audio/wav",
            filename="speech.wav",
            background=lambda: os.unlink(temp_filename)  # Delete file after sending
        )
    
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating speech: {str(e)}"
        )

@app.get("/voices")
async def list_available_voices():
    """List all available TTS voices"""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        voice_list = [
            {
                "id": i,
                "name": voice.name,
                "languages": voice.languages,
                "voice_id": voice.id
            }
            for i, voice in enumerate(voices)
        ]
        
        return {"voices": voice_list}
    
    except Exception as e:
        logger.error(f"Error listing voices: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing voices: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "text-to-speech"}

if __name__ == "__main__":
    logger.info("Starting Text-to-Speech service on port 5007")
    uvicorn.run(app, host="0.0.0.0", port=5007)
