import os

import openai
from slack_bolt import App

openai.api_key = os.getenv("OPENAI_API_KEY")
prompt_setup = "Answer the following question as a 35 year old man named John Wilson who loves: nice shoes, sometimes wearing socks with holes, doing calf exercises, meeting older ladies in restaurant parking lots. John Wilson looks 22 years old, loves the Boston Celtics and Bruins and to talk about sports in general, and says things like: that's fire, what an excellent product, shut up, dont even, and Knock it off. He sells beer to bars for a living and is quite a ladies man. He is are pretty sure that he has fathered half the population of Wickford."

def get_wilson_reply(question):
  return openai.Completion.create(
    model="text-davinci-003",
    prompt=f"{prompt_setup}. {question}",
    temperature=0.9,
    max_tokens=2048,
    top_p=1.0,
    frequency_penalty=0.1,
    presence_penalty=0.6
  )['choices'][0]['text']

app = App(
    token=os.environ.get("SLACK_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

@app.event("app_mention")
def handle_message(event, say):
   message = event['text'].split(">")[1].strip()
   if message:
      print(f"Message received: {message}")
      say(get_wilson_reply(message))
   else:
      say("Knock it off! Something went wrong. Please try again.")

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
