
import time, json, redis, os

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

class ChatHistoryManager:
    _redis_client = None  # Class-level variable to initialize once

    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD):
        if not ChatHistoryManager._redis_client:
            ChatHistoryManager._redis_client = redis.from_url(f"redis://default:{password}@{host}:{port}/0")
        self.redis_client = ChatHistoryManager._redis_client

    def save_message(self, user_id, role, message, save_time=60*60*12):
        """Save the message in Redis with timestamp."""
        history_key = f"chat_history:{user_id}"
        chat_entry = json.dumps({"role": role, "message": message, "timestamp": time.time()})
        self.redis_client.rpush(history_key, chat_entry)
        self.redis_client.expire(history_key, save_time)  # Set expiration for 10 minutes

    def get_recent_chat_history(self, user_id, time_window=60*60):
        """Retrieve messages from the last 'time_window' seconds."""
        history_key = f"chat_history:{user_id}"
        messages = self.redis_client.lrange(history_key, 0, -1)
        recent_messages = []
        
        current_time = time.time()
        for msg in messages:
            msg_data = json.loads(msg)
            if current_time - msg_data["timestamp"] <= time_window:
                recent_messages.append(msg_data)
        recent_messages = [{"role": msg["role"], "content": msg["message"]} for msg in recent_messages]
        return recent_messages

    def clear_chat_history(self, user_id):
        """Delete the chat history of a specific user."""
        history_key = f"chat_history:{user_id}"
        self.redis_client.delete(history_key)
        print(f"Chat history for {user_id} has been cleared.")