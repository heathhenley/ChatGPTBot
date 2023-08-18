# Simple Python ChatBot Implementation
Wrapper around OpenAI's chat completion API. Started working on this for fun, there's
really no reason to use this project instead of [LangChain](https://docs.langchain.com/docs/)
unless you're just trying to find something simple to hack on. I've at least demonstrated
how to wrap and use in a Google Chat bot (in use at work using our Tech Blog as
context), a slack bot (not using any context at the moment) and FastAPI (using my own
blog as context) this a WIP.

## Overview
This is python wrapper to call [OpenAI](https://platform.openai.com/docs/quickstart)'s
completion API to build a chatbot. The prompt can be customized to make it any kind of
chatbot you want (see the example below). Right now, in memory storage is used to store
the last handful of messages so that the bot has some context and some concept of "memory".
Of course it forgets everything on each restart of the server, and there's no checking
to make sure your're not asking for too many tokens yet, so if that happens it will
fail and remove the oldest message from the list.

It is set up to use a Redis DB as a "context cache" or "knowledge store" - so a search
can be done on each query to look for relevant context to give to the model.