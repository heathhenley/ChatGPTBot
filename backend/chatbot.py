import openai
import numpy as np
import redis
from redis.commands.search.query import Query
import tiktoken

DEFAULT_PROMPT = "You're a nice helpful chatbot."
MAX_TOKENS = 16000
GPT_MODEL = "gpt-3.5-turbo-0613"

# From: https://platform.openai.com/docs/guides/chat/introduction
def num_tokens(messages, prompt="", model=GPT_MODEL):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model != GPT_MODEL:
        raise NotImplementedError(f"""num_tokens() is not presently implemented for model {model}.""")
    num_tks = 0
    for message in messages:
        num_tks += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tks += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tks += -1  # role is always required and always 1 token
    num_tks += 2  # every reply is primed with <im_start>assistant
    return num_tks + len(encoding.encode(prompt))


# Search Redis for similar information
# TODO: Some of this is still implemenation specific (I'm storing blog posts
# in redis). Figure out how to make this more generic?
def search_vectors(query_vector, client, top_k=1):
    base_query = f"*=>[KNN {top_k} @embedding $vector AS vector_score]"
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
        self.max_tokens = 500

        
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
        # Trim old messages as we go:
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

    def _get_prompt_with_context(self, context: str) -> str:
        if not context:
            return self.prompt
        return (f"{self.prompt}\nThe information enclosed in "
                      f"backticks will help you answer the query: `{context}`")

    def _trim_to_fit_token_limit(self, message_list: list, context: str) -> str:
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

    def get_reply(self, latest_message: str) -> str:
        """ Get a reply from the chatbot.
        
        Returns a string containing the chatbot's response.
        """
        # Get the full context of the conversation to put it in prompt
        message_list, context = self._get_full_context(latest_message)

        try:
            prompt = self._trim_to_fit_token_limit(message_list, context)
            print(f"{num_tokens(message_list, prompt)} tokens")
            # Call OpenAI's API
            response = openai.ChatCompletion.create(
                model=GPT_MODEL,
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
            # Add the response to the message queue
            self.message_queue.append(response)
            return response["content"]
        except Exception as e:
            print(e)
            raise(e)
      