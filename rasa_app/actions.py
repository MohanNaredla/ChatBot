import logging
import requests
from typing import Any, Text, Dict, List
from dotenv import load_dotenv
import os

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

RAG_SERVICE_URL = os.getenv('RAG_URL')


class ActionGetInfo(Action):
    def name(self) -> Text:
        return "action_get_info"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "")
        if not user_message:
            logger.warning("No user message for action_get_info.")
            return []

        payload = {"question": user_message}
        answer_text = ""
        try:
            response = requests.post(RAG_SERVICE_URL, json=payload, timeout=1000)
            if response.status_code == 200:
                answer_text = response.json().get("answer") or \
                    "I'm sorry, I couldn't find an answer to your question."
            else:
                logger.error(f"RAG service returned status {response.status_code}")
                answer_text = "I'm sorry, I couldn't retrieve the information at the moment."
        except Exception as e:
            logger.error(f"RAG service error: {e}")
            answer_text = "Apologies, I'm having trouble accessing the information right now."

        dispatcher.utter_message(text=answer_text)
        return []