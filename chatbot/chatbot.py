import openai
import numpy as np
import redis
from redis.commands.search.query import Query

from utils import num_tokens

DEFAULT_PROMPT = "You're a nice helpful chatbot."
MAX_TOKENS = 16000
GPT_MODEL = "gpt-3.5-turbo-0613"

# TODO(Heath): Move these classes to their own files / folders based on their
# functionality to make this easier to read / navigate.
class BaseMessageMemory:
    def __init__(self, memory_length: int = 5):
        self.memory_length = memory_length
        self.message_queue = []

    def add_latest_user_query(self):
        raise NotImplementedError

    def add_latest_bot_response(self):
        raise NotImplementedError
    
    def get_message_list(self):
        raise NotImplementedError
    
    def trim_message_list(self):
        raise NotImplementedError


class MessageMemory(BaseMessageMemory):
    """ Stores the conversation history in memory and uses the `memory_length`
    parameter to determine how many messages to send to the API to provide
    context.
    """
    def __init__(self, memory_length: int = 5):
        super().__init__(memory_length)

    def add_latest_user_query(self, latest_message: str):
        self.message_queue.append(
            {"role": "user", "content": latest_message}
        )

    def add_latest_bot_response(self, bot_response: str):
        self.message_queue.append(bot_response)
        self.trim_message_list()

    def get_message_list(self):
        return self.message_queue

    def trim_message_list(self):
        while len(self.message_queue) > self.memory_length:
            self.message_queue.pop(0)


class BaseKnowledgeBase:
    def __init__(self):
        pass

    def get_context(self, user_query: str):
        raise NotImplementedError


class KnowledgeBaseRedis(BaseKnowledgeBase):

    def __init__(self, redis_url: str, api_key: str):
        openai.api_key = api_key
        self.redis_client = redis.from_url(
            redis_url, 
            encoding='utf-8',
            decode_responses=True,
            socket_timeout=3.0)

    def get_context(self, user_query: str) -> str | None:
        # Compute embedding of latest message
        embedding = openai.Embedding.create(
            input=user_query,
            model="text-embedding-ada-002")
        embedding = embedding["data"][0]["embedding"]
        vector = np.array(embedding).astype(np.float32).tobytes()
        # Search Redis for similar information
        return self._search_vectors(vector)

    def _search_vectors(self, query_vector, top_k=1):
        # Nearest neighbor search on query vector in redis db
        base_query = f"*=>[KNN {top_k} @embedding $vector AS vector_score]"
        query = Query(base_query).return_fields("content", "vector_score").sort_by("vector_score").dialect(2)
        try:
            results = self.redis_client.ft("posts").search(query, query_params={"vector": query_vector})
        except Exception as e:
            print("Error calling Redis search: ", e)
            return None
        return results.docs[0].content


class ChatBot:
    """ Wrapper to call OpenAI's GPT-3.5 API and return a response.
    
    Stores the conversation history in memory and uses the `memory_length`
    parameter to determine how many messages to send to the API to provide
    context.
    """
    def __init__(
            self,
            api_key: str,
            prompt: str = DEFAULT_PROMPT,
            message_memory: BaseMessageMemory = MessageMemory(),
            knowledge_base: BaseKnowledgeBase = None,
            gpt_model: str = GPT_MODEL):
        openai.api_key = api_key
        self.prompt = prompt
        self.gpt_model = gpt_model
        self.message_memory = message_memory
        self.knowledge_base = knowledge_base
        self.max_tokens = 500

    def _get_prompt_with_context(self, context: str) -> str:
        if not context:
            return self.prompt
        return (f"""
             {self.prompt}\nThe information enclosed in
             backticks will help you answer the query: `{context}`\n
             The user says: """)

    def _trim_to_fit_token_limit(
      self, message_list: list, context: str) -> str:
        prompt = self._get_prompt_with_context(context)
        while num_tokens(message_list, prompt) > (MAX_TOKENS - self.max_tokens):
            if len(message_list) > 1:
                message_list.pop(0)
                continue
            if len(context) <= 1:
                raise ValueError("Message list and context are too long.")
            print("Message list is too long, but we can't trim it any further.")
            print("Triming context instead.")
            context = context[:len(context)//2]
            prompt = self._get_prompt_with_context(context)
        return prompt

    def get_reply(self, user_query: str) -> str:
        """ Get a reply from the chatbot.
        
        Returns a string containing the chatbot's response.
        """
        self.message_memory.add_latest_user_query(user_query)
        message_list = self.message_memory.get_message_list()
        context = None
        if self.knowledge_base:
            context = self.knowledge_base.get_context(user_query)
        try:
            prompt = self._trim_to_fit_token_limit(
                message_list, context)
            # Call OpenAI's API
            response = openai.ChatCompletion.create(
                model=self.gpt_model,
                messages=[
                    {"role": "user", "content": prompt.strip()},
                    *message_list,
                ],
                temperature=0.5,
                max_tokens=self.max_tokens,
                top_p=1.0,
                frequency_penalty=0.1,
                presence_penalty=0.6
            )["choices"][0]["message"]
            self.message_memory.add_latest_bot_response(response)
            return response["content"]
        except Exception as e:
            print(e)
            raise(e)
      