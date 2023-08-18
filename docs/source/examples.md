# Examples
Here's the simplest basic example of how to use this module, with no custom
prompt, context and the default in memory chat history of only 5 messages.
```python
>>> from chatbot import chatbot
>>> import os
>>> bot = chatbot.ChatBot(api_key=os.getenv("OPENAI_API_KEY"))
>>> bot.get_reply("What's up there chatbot?")
"Hello! I'm here to help you with any questions or problems you may have. How can I assist you today?"
```
For an example of how to use a custom Redis DB as a knowledge store, see the
FastAPI example below. All of the examples here have been deployed on
[railway.app](railway.app), but of course you could use whatever you like.

## Slack Bot
This is a [simple example](https://github.com/heathhenley/ChatGPTBot/tree/main/examples/slack) of how to use this chatbot wrapper to create a slack bot.
If you want to set up your own slack bot, the Slack Bolt API is pretty easy to
use:
- https://slack.dev/bolt-python/tutorial/getting-started
This is running in my personal slack with friends.

## Google Chat Bot
This is an [example](https://github.com/heathhenley/ChatGPTBot/tree/main/examples/google_chat) of how to create a chat bot for your google chat workspace.

## FastAPI
This is [simple FastAPI](https://github.com/heathhenley/ChatGPTBot/tree/main/examples/fast_api) app that uses this module in the backend of a API. This is running
an API that can be used to query OpenAI's completion api but the knowledge base of my
personal blog. Check it out [here](https://heathblogbot.up.railway.app/docs)
