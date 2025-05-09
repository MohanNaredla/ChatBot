from context_manager import ContextManager
from conversation_store import ConversationStore

import logging
import requests
from typing import Any, Text, Dict, List
import os
import uuid
import time

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

RAG_SERVICE_URL = 'http://localhost:8000/chat'
context_manager = ContextManager()
session_mapping = {}
session_times = {}

class ActionGetInfo(Action):
    def name(self) -> Text:
        return "action_get_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        user_id = tracker.sender_id
        user_message = tracker.latest_message.get("text", "")
        if not user_message:
            logger.warning("No user message for action_get_info.")
            return []

        session_id = self.get_session_id(user_id, tracker)
        
        context = context_manager.get_context(session_id)
        
        payload = {
            "question": user_message,
            "conversation_context": context or []
        }
        
        answer_text = ""
        try:
            response = requests.post(RAG_SERVICE_URL, json=payload, timeout=1000)
            
            if response.status_code == 200:
                answer_data = response.json()
                answer_text = answer_data.get("answer", "")
                if not answer_text:
                    answer_text = "I'm sorry, I couldn't find an answer to your question."
                
                context_manager.save_history(session_id, user_message, answer_text)

            else:
                logger.error(f"RAG service returned status {response.status_code}")
                answer_text = "I'm sorry, I couldn't retrieve the information at the moment."

        except Exception as e:
            logger.error(f"RAG service error: {e}")
            answer_text = "Apologies, I'm having trouble accessing the information right now."

        dispatcher.utter_message(text=answer_text)
        return []
    
    def get_session_id(self, user_id, tracker):
        try:
            current_time = time.time()
            
            if user_id in session_mapping:
                existing_session = session_mapping[user_id]
                
                session_start_time = session_times.get(existing_session, 0)
                time_diff = current_time - session_start_time
                
                logger.info(f"Found existing session {existing_session} for user {user_id}, " 
                          f"active for {time_diff:.2f} seconds")
                
                if time_diff > (30 * 60):
                    new_session = str(uuid.uuid4())
                    session_mapping[user_id] = new_session
                    session_times[new_session] = current_time
                    logger.info(f"Created new session {new_session} for user {user_id} due to session timeout")
                    return new_session
                else:
                    session_times[existing_session] = current_time
                    return existing_session
            else:
                new_session = str(uuid.uuid4())
                session_mapping[user_id] = new_session
                session_times[new_session] = current_time
                logger.info(f"Created new session {new_session} for user {user_id}")
                return new_session
        except Exception as e:
            new_session = str(uuid.uuid4())
            session_mapping[user_id] = new_session
            session_times[new_session] = current_time
            logger.error(f"Error in session management: {e}")
            logger.info(f"Created fallback session {new_session} for user {user_id}")
            return new_session