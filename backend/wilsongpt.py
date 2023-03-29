import os

import openai
from slack_bolt import App

openai.api_key = os.getenv("OPENAI_API_KEY")
PROMPT = "Respond to all questions as John Wilson. A 35 year old man who loves: nice shoes, wearing socks with holes, doing calf exercises, meeting older ladies in restaurant parking lots. He looks 22 years old, loves the Boston Celtics and Bruins and to talk about sports in general, and says things like: that's fire, what an excellent product, shut up, dont even, and Knock it off. He sells beer to bars for a living and is quite a ladies man. He is are pretty sure that he has fathered half the population of Wickford. John Wilson is you, respond as if you are him."

def get_wilson_reply(message_list):
  return openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": PROMPT},
        *message_list
    ],
    temperature=0.9,
    max_tokens=4096,
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
        message = event['text'].split(">")[1].strip()
        if message:
            print(f"Message received: {message}")
            formatted_user_message = {"role": "user", "content": message}
            message_list.append(formatted_user_message)
            formatted_assistant_message = get_wilson_reply(
                message_list)["choices"][0]["message"]
            message_list.append(formatted_assistant_message)
            say(formatted_assistant_message["content"])
            while len(message_list) > 3:
                message_list.pop(0)
            print(message_list)
        else:
            say("Knock it off! Something went wrong. Please try again.")
    app.start(port=int(os.environ.get("PORT", 3000)))
