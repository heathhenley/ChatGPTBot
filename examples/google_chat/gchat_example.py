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
A basic Hangouts Chat bot to interface with OpenAI's GPT-3.5 API.
"""
import logging
import os

import openai
from flask import Flask, json, request

import chatbot

# Globals
app = Flask(__name__)
bot = chatbot.ChatBot(
    api_key=os.getenv("OPENAI_API_KEY"),
    prompt=os.getenv("PROMPT", chatbot.DEFAULT_PROMPT),
    memory_length=5)

@app.route('/', methods=['POST'])
def home_post():
    """Respond to POST requests to this endpoint.
    All requests sent to this endpoint from Hangouts Chat are POST
    requests.
    """
    data = request.get_json()
    if data['type'] == 'REMOVED_FROM_SPACE':
        logging.info('Bot removed from a space')
        return None
    resp_dict = {'text' : format_response(data)}
    return json.jsonify(resp_dict)


def format_response(event):
    """Determine what response to provide based upon event data.
    Args:
      event: A dictionary with the event data.
    """
    # Case 1: The bot was added to a room
    if event['type'] == 'ADDED_TO_SPACE' and event['space']['type'] == 'ROOM':
        return f"Thanks for adding me to {event['space']['displayName']}!"
    # Case 2: The bot was added to a DM
    if event['type'] == 'ADDED_TO_SPACE' and event['space']['type'] == 'DM':
        return f"Thanks for adding me to a DM, {event['user']['displayName']}!"
    # Case 3: The bot got a message
    if event['type'] == 'MESSAGE':
        try:
            return bot.get_reply(event['message']['text'])
        except Exception as e:
            print(e)
            return "I seem to have hit an uncharted obstacle. Please try again."


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=80, debug=True)