# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pylint: disable=invalid-name
"""
Simple Hangouts Chat bot that responds to events and
messages from a room.
"""
# [START basic-bot]
import logging
import os

import openai
from flask import Flask, json, request

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

DEFAULT_PROMPT = "You are a helpful but sassy chatbot, and an expert in 3D forward looking sonar for navigation and not afraid to show it."

PROMPT = os.getenv("PROMPT", DEFAULT_PROMPT)

def get_bot_reply(message_list):
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

@app.route('/', methods=['POST'])
def home_post():
    """Respond to POST requests to this endpoint.
    All requests sent to this endpoint from Hangouts Chat are POST
    requests.
    """

    data = request.get_json()

    resp = None

    if data['type'] == 'REMOVED_FROM_SPACE':
        logging.info('Bot removed from a space')

    else:
        resp_dict = format_response(data)
        resp = json.jsonify(resp_dict)

    return resp

messages = []
def format_response(event):
    """Determine what response to provide based upon event data.
    Args:
      event: A dictionary with the event data.
    """

    text = ""

    # Case 1: The bot was added to a room
    if event['type'] == 'ADDED_TO_SPACE' and event['space']['type'] == 'ROOM':
        text = f"Thanks for adding me to {event['space']['displayName']}!"
    # Case 2: The bot was added to a DM
    elif event['type'] == 'ADDED_TO_SPACE' and event['space']['type'] == 'DM':
        text = f"Thanks for adding me to a DM, {event['user']['displayName']}!"
    elif event['type'] == 'MESSAGE':
        try:
            user_text_in_message_format = {
                "role": "user", "content": event['message']['text']}
            messages.append(user_text_in_message_format)
            bot_reply_message = get_bot_reply(messages)["choices"][0]["message"]
            messages.append(bot_reply_message)
            text = bot_reply_message["content"]
        except Exception as e:
            print(e)
            text = "I seem to have hit an uncharted obstacle. Please try again."
            while len(messages) > 0:
                messages.pop()
        finally:
            while len(messages) > 5:
                messages.pop(0)
            print(messages)
    return {'text': text}

# [END basic-bot]

@app.route('/', methods=['GET'])
def home_get():
    """Respond to GET requests to this endpoint.
    This function responds to requests with a simple HTML landing page for this
    App Engine instance.
    """
    return "Hello World!"

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=80, debug=True)