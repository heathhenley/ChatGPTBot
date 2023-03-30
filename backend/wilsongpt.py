import os

import openai
from slack_bolt import App

openai.api_key = os.getenv("OPENAI_API_KEY")
DEFAULT_PROMPT = "Respond to all questions as John Wilson. A 35 year old man who loves: nice shoes, wearing socks with holes, doing calf exercises, meeting older ladies in restaurant parking lots. He looks 22 years old, loves the Boston Celtics and Bruins and to talk about sports in general, and says things like: that's fire, what an excellent product, shut up, dont even, and knock it off. He sells beer to bars for a living and is quite a ladies man. He is are pretty sure that he has fathered half the population of Wickford. John Wilson also likes to say LET'S F'ing GO emphatically. One or twice has been known to eat mashed potatoes with his hands and he HATES coors lite. John Wilson's nemesis is Dan. Respond in a tone that conveys you want to help, but you're also annoyed that people keep asking you so many questions."
PROMPT = os.getenv("PROMPT", DEFAULT_PROMPT)

def get_wilson_reply(message_list):
  return openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": PROMPT},
        *message_list
    ],
    temperature=0.9,
    max_tokens=3000,
    top_p=1.0,
    frequency_penalty=0.1,
    presence_penalty=0.6
  )


if __name__ == "__main__":
    app = App(
        token=os.environ.get("SLACK_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))
    message_list = []
    @app.event("app_mention")
    def handle_message(event, say):
        message = event['text']
        if message:
            try:
                print(f"Message received: {message}")
                message = message.replace("<@U050ADS01RD>", "John Wilson")
                message = f"You are John Wilson, respond to this message as he would. Do not deviate from his character. {message}"
                formatted_user_message = {"role": "user", "content": message}
                message_list.append(formatted_user_message)
                formatted_assistant_message = get_wilson_reply(
                    message_list)["choices"][0]["message"]
                message_list.append(formatted_assistant_message)
                say(formatted_assistant_message["content"])
                while len(message_list) > 5:
                    message_list.pop(0)
                print(message_list)
            except Exception as e:
                print(e)
                say("You son of a.... something went wrong 🙃.")
        else:
            say("Knock it off! Something went wrong. Please try again.")
            message_list.pop(0)
    app.start(port=int(os.environ.get("PORT", 3000)))
