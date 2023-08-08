import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import chatbot

app = FastAPI()

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
  redis_string=os.getenv("REDIS_URL"),
  memory_length=1)

@app.get("/chatbot")
def read_root(user_query: str) -> str:
    return bot.get_reply(user_query)
