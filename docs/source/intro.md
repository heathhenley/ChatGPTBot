# Simple Python ChatBot Implementation
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
