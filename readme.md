# Simple ChatBot Wrapper
## Simple Python ChatBot Implementation
Wrapper around OpenAI's chat completion API. Started working on this for fun, there's
really no reason to use this project instead of [LangChain](https://docs.langchain.com/docs/)
unless you're just trying to find something simple to hack on. I've at least demonstrated
how to wrap and use in a Google Chat bot (in use at work using our Tech Blog as
context), a slack bot (not using any context at the moment) and FastAPI (using my own
blog as context) this a WIP.

## Overview
Chatbot module to interface with OpenAI's API and add some common chat functionality:
- save a short message history
- add a knowledge base and use it to find relevant data based on vector similarity (also
  using OpenAI for the embeddings)
- examples of how to interface with Slack, Google Chat, and create a FastAPI REST API

## Examples
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
[railway.app](railway.app), but you could use whatever you like.

### Installation
Currently you can only "install" by `git clone`ing the repo, and
`pip install -r requirements.txt` the requirements (probably in a venv). Each
example has it's own requirements.txt file, so you'll need to install those for
whatever example you want to run.

### Slack Bot
This is a [simple example](https://github.com/heathhenley/ChatGPTBot/tree/main/examples/slack) of how to use this chatbot wrapper to create a slack bot.
If you want to set up your own slack bot, the Slack Bolt API is pretty easy to
use: 
- https://slack.dev/bolt-python/tutorial/getting-started
This is running in my personal slack with friends.

### Google Chat Bot
This is [an example](https://github.com/heathhenley/ChatGPTBot/tree/main/examples/google_chat) of how to create a chat bot for your google chat workspace.

### FastAPI
This is [simple FastAPI](https://github.com/heathhenley/ChatGPTBot/tree/main/examples/fast_api) app that uses this module in the backend of a API. This is running
an API that can be used to query OpenAI's completion api but the knowledge base of my
personal blog. Check it out [here](https://heathblogbot.up.railway.app/docs)
