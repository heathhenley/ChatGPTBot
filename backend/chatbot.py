import os
import openai
import numpy as np
import redis
from redis.commands.search.query import Query

DEFAULT_PROMPT = "You're a nice helpful chatbot."

# Search Redis for similar information
# TODO: Some of this is still implemenation specific (I'm storing blog posts
# in redis). Figure out how to make this more generic?
def search_vectors(query_vector, client, top_k=5):
    base_query = "*=>[KNN 5 @embedding $vector AS vector_score]"
    query = Query(base_query).return_fields("content", "vector_score").sort_by("vector_score").dialect(2)
    try:
        results = client.ft("posts").search(query, query_params={"vector": query_vector})
    except Exception as e:
        print("Error calling Redis search: ", e)
        return None
    return results


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
            memory_length: int = 5,
            custom_append_message: str = None,
            redis_string: str = None):
        openai.api_key = api_key
        self.prompt = prompt
        self.memory_length = memory_length
        self.message_queue = []
        self.custom_append_message = custom_append_message
        self.redis_client = None
        if redis_string:
            self.redis_client = redis.from_url(
                redis_string, 
                encoding='utf-8',
                decode_responses=True,
                socket_timeout=3.0)

        
    def _get_full_context(self, latest_message: str) -> tuple[list, str]:
        """ Get the full context of the conversation
        
        Returns latest messages based on memory length and adds the
        latest message to memory.

        Returns a str containing relevant information from redis to provide
        context to the chatbot.
        """
        additional_context = self._get_additional_context(latest_message)
        if self.custom_append_message:
          latest_message = self.custom_append_message + latest_message
        self.message_queue.append(
            {"role": "user", "content": latest_message}
        )
        while len(self.message_queue) > self.memory_length:
            self.message_queue.pop(0)
        return self.message_queue, additional_context

    def _get_additional_context(self, latest_message: str) -> str:
        """ Find the most similar information in redis db to provide context."""
        if not self.redis_client:
            return ""
        # Compute embedding of latest message
        embedding = openai.Embedding.create(
            input=latest_message,
            model="text-embedding-ada-002")
        embedding = embedding["data"][0]["embedding"]
        vector = np.array(embedding).astype(np.float32).tobytes()
        # Search Redis for similar information
        return search_vectors(vector, self.redis_client).docs[0].content

    def get_reply(self, latest_message: str) -> str:
        """ Get a reply from the chatbot.
        
        Returns a string containing the chatbot's response.
        """
        # Get the full context of the conversation
        message_list, context = self._get_full_context(latest_message)
        prompt = (f"{self.prompt}\n The information enclosed in "
                  f"backticks, may be relevant to the query: `{context}`")
        try:
            # Call OpenAI's API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt},
                    *message_list,
                ],
                temperature=0.9,
                max_tokens=3000,
                top_p=1.0,
                frequency_penalty=0.1,
                presence_penalty=0.6
            )["choices"][0]["message"]
            # Add the response to the message queue
            self.message_queue.append(response)
            return response["content"]
        except Exception as e:
            print(e)
            # pop a message off the queue - usually raising here is due to
            # requesting too many tokens from the api.
            if self.message_queue:
                self.message_queue.pop(0)
            # reraise so client can handle
            raise(e)
      