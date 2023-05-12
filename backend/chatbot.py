import os
import openai

DEFAULT_PROMPT = "You're a nice helpful chatbot."

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
            custom_append_message: str = None):
        openai.api_key = api_key
        self.prompt = prompt
        self.memory_length = memory_length
        self.message_queue = []
        self.custom_append_message = custom_append_message
        
    def _get_full_context(self, latest_message: str) -> list:
        """ Get the full context of the conversation
        
        Returns latest messages based on memory length and adds the
        latest message to memory.

        NOTE(Heath): This seems a little unnecessary at the moment -
        we're adding the latest message to the queue, which is a data
        member of the class, and then just returning it. But later, instead
        of retuning just the 5 latest messages in the queue,
        we'll be returning a custom context based on the latest message.
        """
        if self.custom_append_message:
          latest_message = self.custom_append_message + latest_message
        self.message_queue.append(
            {"role": "user", "content": latest_message}
        )
        while len(self.message_queue) > self.memory_length:
            self.message_queue.pop(0)
        return self.message_queue

    def get_reply(self, latest_message: str) -> str:
        """ Get a reply from the chatbot.
        
        Returns a string containing the chatbot's response.
        """
        # Get the full context of the conversation
        message_list = self._get_full_context(latest_message)
        try:
            # Call OpenAI's API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": self.prompt},
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
      