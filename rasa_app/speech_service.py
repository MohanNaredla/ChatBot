"""
Combined Speech-to-Text module for the chatbot application.
Based on the SpeechBot implementation, providing both direct microphone listening
and uploaded audio file processing capabilities.
"""
import speech_recognition as sr
import tempfile
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pydantic import BaseModel
from typing import Optional
import threading
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Speech_Service")

app = FastAPI(title="Speech Service",
              description="Combined service for speech processing in the chatbot")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class SpeechResponse(BaseModel):
    """Response model for speech processing"""
    text: str
    confidence: float = 0.0
    error: Optional[str] = None

class ListenRequest(BaseModel):
    """Request model for listening to speech"""
    duration: int = 5  # Default listening duration in seconds
    language: str = "en-US"  # Default language

# Queue to store the latest transcription result
transcription_queue = queue.Queue()

# Global recognizer object
recognizer = sr.Recognizer()

@app.post("/stt", response_model=SpeechResponse)
async def convert_speech_to_text(audio_file: UploadFile = File(...)):
    """
    Process uploaded audio file and convert to text
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            # Write the file content
            content = await audio_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
            
        logger.info(f"Audio saved to temporary file: {temp_path}")
            
        # Process the file with a recognizer
        try:
            # Try to recognize directly
            with sr.AudioFile(temp_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                logger.info(f"Recognized text: {text}")
                return SpeechResponse(text=text, confidence=0.9)
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            return SpeechResponse(
                text="", 
                confidence=0.0, 
                error=f"Error processing audio: {str(e)}"
            )
    finally:
        # Clean up temp file
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            logger.error(f"Error removing temp file: {e}")

@app.post("/listen", response_model=SpeechResponse)
async def listen_and_transcribe(request: ListenRequest):
    """
    Listen directly to microphone input and transcribe
    """
    # Clear the queue
    while not transcription_queue.empty():
        transcription_queue.get()
    
    # Start listening in a separate thread
    thread = threading.Thread(
        target=listen_in_thread, 
        args=(request.duration, request.language)
    )
    thread.daemon = True
    thread.start()
    
    # Wait for the transcription result
    try:
        # Wait a bit longer than the requested duration
        result = transcription_queue.get(timeout=request.duration + 5)  
        return result
    except queue.Empty:
        logger.error("Timed out waiting for transcription")
        return SpeechResponse(
            text="", 
            confidence=0.0, 
            error="Timed out waiting for transcription"
        )

def listen_in_thread(duration: int, language: str):
    """Listen to microphone input and transcribe in a separate thread"""
    try:
        with sr.Microphone() as source:
            logger.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)
            logger.info(f"Listening for {duration} seconds...")
            audio = recognizer.listen(source, timeout=duration)
            
            logger.info("Recognizing...")
            try:
                text = recognizer.recognize_google(audio, language=language)
                logger.info(f"Recognized text: {text}")
                transcription_queue.put(SpeechResponse(text=text, confidence=0.9))
            except sr.UnknownValueError:
                logger.warning("Speech recognition could not understand audio")
                transcription_queue.put(SpeechResponse(
                    text="", 
                    confidence=0.0, 
                    error="Could not understand audio"
                ))
            except sr.RequestError as e:
                logger.error(f"Could not request results from speech recognition service; {e}")
                transcription_queue.put(SpeechResponse(
                    text="", 
                    confidence=0.0, 
                    error=f"Speech recognition service unavailable: {str(e)}"
                ))
    except Exception as e:
        logger.error(f"Error in speech recognition: {e}")
        transcription_queue.put(SpeechResponse(
            text="", 
            confidence=0.0, 
            error=f"Error in speech recognition: {str(e)}"
        ))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "speech-service",
        "capabilities": ["stt", "listen"]
    }

if __name__ == "__main__":
    logger.info("Starting Speech Service on port 5006")
    uvicorn.run(app, host="0.0.0.0", port=5006)
