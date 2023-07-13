import argparse
import os
import numpy as np
import openai
import redis

import read_blog as rb

BLOG_URL = r"https://www.farsounder.com/blog"

openai.api_key = os.getenv("OPENAI_API_KEY")

def add_text_to_redis(db, text, url):
    """ Add text, url, and embedding to redis db."""
    # Get the embedding for the text
    embedding = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    vector = embedding["data"][0]["embedding"]
    vector = np.array(vector).astype(np.float32).tobytes()
    post_hash = {
        "url": url,
        "content": text,
        "embedding": vector
    }
    db.hset(name=f"blog:{url}", mapping=post_hash)

def _add_farsounder_blog_to_redis(db):
    pipeline = db.pipeline(transaction=False)
    print("Parsing blog...")
    for url in rb.get_list_of_blog_urls(BLOG_URL):
        text = rb.get_blog_text_for_url(url)
        add_text_to_redis(db, text, url)
    pipeline.execute()

def add_file_to_redis(db, filename):
    """ This assumes the file is hash0|text0\nhash1|text1\n..."""
    pipeline = db.pipeline(transaction=False)
    print("Parsing file..")
    with open(filename, "r") as f:
        for line in f.readlines():
            tag, text = line.strip().split("|")
            print(tag, text)
            add_text_to_redis(db, text, tag)
    pipeline.execute()

def index_blog():
    print("connecting to Redis...")
    redis_client = redis.from_url(url=os.getenv("REDIS_URL", ""), 
        encoding='utf-8',
        decode_responses=True,
        socket_timeout=30.0)
    print("checking Redis connection...")
    if not redis_client or not redis_client.ping():
        raise Exception("Redis connection failed")
    print("Connected to Redis")

    # Index FarSounder blog
    _add_farsounder_blog_to_redis(redis_client)


def index_faqs_file():
    redis_client = redis.from_url(url=os.getenv("REDIS_URL", ""), 
        encoding='utf-8',
        decode_responses=True,
        socket_timeout=30.0)
    print("checking Redis connection...")
    if not redis_client or not redis_client.ping():
        raise Exception("Redis connection failed")
    print("Connected to Redis")
    # Index FarSounder blog
    add_file_to_redis(redis_client, "../context_data/faqs.csv")


def main():
    print("connecting to Redis...")
    redis_client = redis.from_url(url=os.getenv("REDIS_URL", ""), 
        encoding='utf-8',
        decode_responses=True,
        socket_timeout=30.0)
    print("checking Redis connection...")
    if not redis_client or not redis_client.ping():
        raise Exception("Redis connection failed")
    print("Connected to Redis")
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str,
        help=("File to add to redis, in the format: "
              "hash0|text0\nhash1|text1\n... the hash can be anything unique, "
              "like a url or a number, a faq number, etc."))
    args = parser.parse_args()
    if args.file:
        add_file_to_redis(redis_client, args.file)


if __name__ == "__main__":
    main()