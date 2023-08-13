import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatbot import chatbot

description = """
This is a simple API that uses OpenAI's GPT-3.5 API to answer questions about
my personal blog. The API is built using FastAPI and deployed on Railway. This
is an example of the simple chatbot module that I put together as a learning
exercise.
"""

app = FastAPI(
  title="Chatbot API - Heath's Blog",
  description=description,
  contact={
    "name": "Heath Henley",
    "url": "https://github.com/heathhenley/ChatGPTBot",
    "email": "heath.j.henley@gmail.com"
  })

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prompt = """You are a helpful chatbot for Heath Henley's personal blog. The
most relevant information from the blog to the query from the user is enclosed. Please answer the user's query using the information from the blog, if the information is not sufficient, please ask the user for more information.\n"""
bot = chatbot.ChatBot(
  api_key=os.getenv("OPENAI_API_KEY"),
  prompt=prompt,
  message_memory=chatbot.MessageMemory(memory_length=1),
  knowledge_base=chatbot.KnowledgeBaseRedis(
      redis_url=os.getenv("REDIS_URL"),
      api_key=os.getenv("OPENAI_API_KEY"))
)

@app.get("/")
def search_blog(user_query: str) -> str:
  """ Search the blog for relevant information and return a response.

  Gets the most relevant information from the blog to the query
  and uses it as context when generating the response."""
  return bot.get_reply(user_query)
