"""
Speech-to-Text module for the chatbot application.
This module provides a FastAPI endpoint to handle audio data from the chatbot UI
and convert it to text using the SpeechRecognition library.
"""
import speech_recognition as sr
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pydantic import BaseModel
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("STT_Service")

app = FastAPI(title="Speech-to-Text Service",
              description="Service for converting speech to text for the chatbot UI")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class SpeechToTextResponse(BaseModel):
    """Response model for speech-to-text conversion"""
    text: str
    confidence: float = 0.0
    error: Optional[str] = None

@app.post("/stt", response_model=SpeechToTextResponse)
async def speech_to_text():
    """
    Listen directly to microphone and transcribe when requested from the UI
    
    Returns:
        SpeechToTextResponse: The transcribed text
    """
    try:
        recognizer = sr.Recognizer()
        
        with sr.Microphone() as source:
            logger.info("UI requested microphone input - adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)
            
            logger.info("Listening...")
            audio = recognizer.listen(source, timeout=5)
            
            logger.info("Recognizing...")
            text = recognizer.recognize_google(audio)
            logger.info(f"Recognized text: {text}")
            
            return SpeechToTextResponse(text=text, confidence=0.9)
            
    except sr.UnknownValueError:
        logger.warning("Could not understand audio")
        return SpeechToTextResponse(text="", confidence=0.0, error="Could not understand audio")
        
    except sr.RequestError as e:
        logger.error(f"Could not request results from Google Speech Recognition service; {e}")
        return SpeechToTextResponse(text="", confidence=0.0, error=str(e))
        
    except Exception as e:
        logger.error(f"Error in speech recognition: {e}")
        return SpeechToTextResponse(text="", confidence=0.0, error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "speech-to-text"}

# No need for startup event anymore since we removed file processing

if __name__ == "__main__":
    logger.info("Starting Speech-to-Text service on port 5006")
    uvicorn.run(app, host="0.0.0.0", port=5006)
