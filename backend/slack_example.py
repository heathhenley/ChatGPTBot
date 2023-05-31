""" Example of a Slackbot using OpenAI's GPT-3.5 API to impersonate a character."""
import os
from slack_bolt import App

import chatbot

if __name__ == "__main__":
    # Use general GPT chatbot wrapper to create a chatbot instance, give it
    # a prompt that we store in an environment variable for now. It should
    # be a blurb that describes the character of the chatbot - in this
    # case, John Wilson.
    bot = chatbot.ChatBot(
        api_key=os.getenv("OPENAI_API_KEY"),
        prompt=os.getenv("PROMPT", chatbot.DEFAULT_PROMPT),
        memory_length=5,
        custom_append_message="You are John Wilson, respond to this message as he would. Do not deviate from his character.")
    
    app = App(
        token=os.environ.get("SLACK_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))
    
    # Handle messages that mention the bot in any channel where the bot is
    # invited. Check the slack docs for all the event types that can be
    # handled.
    @app.event("app_mention")
    def handle_message(event, say):
        message = event['text']
        if message:
            try:
                say(bot.get_reply(message))
            except Exception as e:
                print(e)
                say("You son of a.... something went wrong 🙃.")
        else:
            say("Knock it off! Something went wrong. Please try again.")
    
    # Start the app
    app.start(port=int(os.environ.get("PORT", 3000)))
