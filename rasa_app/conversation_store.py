import json
import os
import logging
from pathlib import Path
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConversationStore:
    def __init__(self, storage_dir='conversation_history', session_expiry_hours=4):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        self.session_expiry = session_expiry_hours * 3600

        self.cleanup_history()

    def get_history(self, session_id):
        history_path = self.storage_dir / f'{session_id}.json'

        if not history_path.exists():
            return []
        
        try:
            with open(history_path, 'r') as f:
                session_data = json.load(f)

                if self.is_session_expired(session_data):
                    os.remove(history_path)
                    return []
                
                return session_data.get('history', [])

        except Exception as e:
            logger.error(f'Unable to read the file {e}')
            return []


    def save_history(self, session_id, history):
        history_path = self.storage_dir / f'{session_id}.json'

        try:
            session_data = {
                'history': history,
                'start_time': time.time()
            }

            with open(history_path, 'w') as f:
                json.dump(session_data, f)
        
        except Exception as e:
            logger.error(f'Unable to save history {e}')


    def is_session_expired(self, session_data):
        session_duration = time.time() - session_data.get('start_time', 0)
        return session_duration >= self.session_expiry
    

    def cleanup_history(self):
        try:
            for file in self.storage_dir.glob('*.json'):
                try:
                    with open(file, 'r') as f:
                        session_data = json.load(f)

                    if self.is_session_expired(session_data=session_data):
                        os.remove(file)

                except Exception as e:
                    logger.error("Can't process the file so removing it")
                    os.remove(file)

        except Exception as e:
            logger.error(f"Error during cleanup {e}")