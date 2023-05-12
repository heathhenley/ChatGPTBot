# Simple ChatBot Wrapper
This is python wrapper to call [OpenAI](https://platform.openai.com/docs/quickstart)'s complettion API to build a chatbot. The prompt can
be customized to make it any kind of chatbot you want (see the example below). Right now,
in memory storage is used to store the last handful of messages so that the bot has some
context and some concept of "memory". Of course it forgets everything on each restart, and there's
no checking to make sure your're not asking for too many tokens yet, so if that happens it will fail
and remove the oldest message from the list.

The next steps will be stick the message history somewhere persistent (based on my comfort
levels I'm going to pick Postgres or Redis) so that it's kept between restarts. Then taking it
a step further, we can compute embeddings for the messages,
and then use the embeddings of the query to search for the most relevant messages
from the chat history to pass those in as context. This same approach can be used to make
you bot an "expert" on whatever you're interested in, just compute embeddings for that
thing (say your blog, website, etc) and look for the most similar entries to the query to
pass as context.

## Examples
### WilsonGPT - An AI Slack Bot to razz our good friend John on Slack

This is a simple example of how to use this chatbot wrapper to create a slack bot.
If you want to set up your own slack bot, the Slack Bolt API is pretty easy to
use: 
- https://slack.dev/bolt-python/tutorial/getting-started

It's set up to run on [Railway](railway.app) in this case (see /backend/railway.toml) for the config
and the required ENV variables with OpenAI and Slack secrets.
