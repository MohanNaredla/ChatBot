from conversation_store import ConversationStore


class ContextManager:
    def __init__(self):
        self.conversation_store = ConversationStore()
        self.max_history_turns = 5


    def get_context(self, session_id):
        history = self.conversation_store.get_history(session_id)
        return history[-self.max_history_turns:]
    

    def save_history(self, session_id, question, answer):
        history = self.conversation_store.get_history(session_id)

        if self.is_valid(answer):
            history.append({
                'question': question,
                'answer': answer
            })

        self.conversation_store.save_history(session_id=session_id, history=history[-self.max_history_turns:])
    

    def is_valid(self, answer):
        invalid_phrases = [
            "I don't have enough information",
            "I couldn't find",
            "I am sorry, I don't know",
            "I am having trouble",
            "Out of context"
        ]

        return not any(phrase.lower() in answer.lower() for phrase in invalid_phrases)