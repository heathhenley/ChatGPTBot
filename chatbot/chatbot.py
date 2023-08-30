import openai
import numpy as np
import redis
from redis.commands.search.query import Query

from chatbot.utils import num_tokens


DEFAULT_PROMPT = "You're a nice helpful chatbot."
MAX_TOKENS = 16000
GPT_MODEL = "gpt-3.5-turbo-0613"


class BaseMessageMemory:
    """Base class for storing the conversation history. This interface is
    assumed to be implemented by the :class:`ChatBot`, so any new child
    classes must implement these methods.

    :param memory_length: The number of messages to store in the chat history,
        defaults to 5
    :type memory_length: int, optional
    """
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
    """Stores the conversation history in memory and uses the `memory_length`
    parameter to determine how many messages to send to the API to provide
    context.

    :param memory_length: The number of messages to store in the chat history,
        defaults to 5
    :type memory_length: int, optional
    """

    def __init__(self, memory_length: int = 5):
        """ Constructor method"""
        super().__init__(memory_length)


    def add_latest_user_query(self, latest_message: str):
        """Add the latest user query to the message queue.
        
        :param latest_message: The latest user query
        :type latest_message: str
        """
        self.message_queue.append(
            {"role": "user", "content": latest_message}
        )

    def add_latest_bot_response(self, bot_response: str):
        """Add the latest bot response to the message queue.

        :param bot_response: The latest bot response
        :type bot_response: str
        """
        self.message_queue.append(bot_response)
        self.trim_message_list()

    def get_message_list(self) -> list[dict]:
        """Returns the message queue.
        :return: The message queue
        :rtype: list[dict]
        """
        return self.message_queue

    def trim_message_list(self):
        """Trims the message list to ``memory_length``."""
        while len(self.message_queue) > self.memory_length:
            self.message_queue.pop(0)


class BaseKnowledgeBase:
    """Base class for a knowledge base. This interface is assumed to be
    implemented by the :class:`ChatBot`, so any new child classes must
    implement these methods.
    """

    def __init__(self):
        pass

    def get_context(self, user_query: str):
        raise NotImplementedError


class KnowledgeBaseRedis(BaseKnowledgeBase):
    """A knowledge base that uses Redis to store information and the embeddings
    for each piece of information. This class uses Redis' vector search to find
    the most similar information to the user's query.

    :param redis_url: The URL for the Redis instance
    :type redis_url: str
    :param api_key: The API key for OpenAI's API
    :type api_key: str
    """
    def __init__(self, redis_url: str, api_key: str):
        openai.api_key = api_key
        self.redis_client = redis.from_url(
            redis_url, 
            encoding='utf-8',
            decode_responses=True,
            socket_timeout=3.0)

    def get_context(self, user_query: str) -> tuple[str, str] | None:
        """Get the context for the user's query.

        :param user_query: The user's query
        :type user_query: str
        :return: The context for the user's query
        :rtype: str | None
        """
        # Compute embedding of latest message
        embedding = openai.Embedding.create(
            input=user_query,
            model="text-embedding-ada-002")
        embedding = embedding["data"][0]["embedding"]
        vector = np.array(embedding).astype(np.float32).tobytes()
        return self._search_vectors(vector)

    def _search_vectors(self, query_vector: np.ndarray, top_k=1) -> str | None:
        """ Search Redis for similar vectors. Not meant to be called directly,
        only implemented as a helper method for `get_context`.

        :param query_vector: The vector to search for
        :type query_vector: np.ndarray
        :param top_k: The number of results to return, defaults to 1
        :type top_k: int, optional
        :return: The most similar vector
        :rtype: str | None
        """
        # Nearest neighbor search on query vector in redis db
        base_query = f"*=>[KNN {top_k} @embedding $vector AS vector_score]"
        query = Query(base_query).return_fields("content", "vector_score").sort_by("vector_score").dialect(2)
        try:
            results = self.redis_client.ft("posts").search(query, query_params={"vector": query_vector})
        except Exception as e:
            print("Error calling Redis search: ", e)
            return None
        url = results.docs[0].id.replace("blog:", "")
        content = results.docs[0].content
        return url, content


class ChatBot:
    """ Wrapper to call OpenAI's GPT-3.5 API and return a response. Optionally
    uses child class implementation of :class:`BaseMessageMemory` and
    :class:`BaseKnowledgeBase` classes to configure how memory is stored and
    how to get context for the user's query.

    :param api_key: The API key for OpenAI's API
    :type api_key: str
    :param prompt: The prompt to use when calling OpenAI's API, defaults to
        "You're a nice helpful chatbot." You will probably want to change this
        to make the chatbot more interesting.
    :type prompt: str, optional
    :param message_memory: The message memory to use, defaults to
        :class:`MessageMemory` - which is a simple in-memory implementation.
    :type message_memory: :class:`BaseMessageMemory`, optional
    :param knowledge_base: The knowledge base to use, defaults to None. If you
        want to use a knowledge base, you must implement the
        :class:`BaseKnowledgeBase`, or use the :class:`KnowledgeBaseRedis`.
    :type knowledge_base: :class:`BaseKnowledgeBase`, optional
    :param gpt_model: The GPT model to use, defaults to "gpt-3.5-turbo-0613".
    :type gpt_model: str, optional
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
        """ Returns the prompt with the context appended to it. This method is
        not intended to be called directly, only implemented as a helper method.

        :param context: The context to append to the prompt
        :type context: str
        :return: The prompt with the context appended to it
        :rtype: str
        """
        if not context:
            return self.prompt
        return (f"""
             {self.prompt}\nThe information enclosed in
             backticks will help you answer the query: `{context}`\n
             The user says: """)

    def _trim_to_fit_token_limit( 
      self, message_list: list, context: str) -> str:
        """Trims the message list and context to fit within the token limit.
        This method is not intended to be called directly, only implemented as
        a helper method.
        
        :param message_list: The message list
        :type message_list: list
        :param context: The context
        :type context: str
        :return: The prompt with the context appended to it
        :rtype: str
        """
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
        """Get a reply from the chatbot.

        :param user_query: The user's query
        :type user_query: str
        :return: The chatbot's response
        :rtype: str
        """
        self.message_memory.add_latest_user_query(user_query)
        message_list = self.message_memory.get_message_list()
        url, context = None, None
        if self.knowledge_base:
            url, context = self.knowledge_base.get_context(user_query)
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
            response = response["content"]
            if url:
                link_text = "This link was used to generate an answer"
                response = f"{response}\n\n{link_text}: {url}"
            return response
        except Exception as e:
            print(e)
            raise(e)
      
