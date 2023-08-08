import os
import redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
 
r = redis.from_url(url=os.getenv("REDIS_URL", ""),
    encoding='utf-8',
    decode_responses=True)
 
SCHEMA = [
    TextField("url"),
    VectorField("embedding", "HNSW", {"TYPE": "FLOAT32", "DIM": 1536, "DISTANCE_METRIC": "COSINE"}),
]
 
# Create the index
try:
    r.ft("posts").create_index(fields=SCHEMA, definition=IndexDefinition(prefix=["blog:"], index_type=IndexType.HASH))
except Exception as e:
    print(e)
    print("Index already exists")