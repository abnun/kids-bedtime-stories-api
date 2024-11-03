# import standard
import os

# import pymongo
from motor.motor_asyncio import AsyncIOMotorClient

CONNECTION_STRING = os.environ.get("MONGO_DB_URL")
DB_NAME = "kids-bedtime-stories"

# DEV DB
client_async = AsyncIOMotorClient(CONNECTION_STRING)
db_async = client_async[DB_NAME]


# Send a ping to confirm a successful connection
try:
    client_async.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")

    characters = db_async["characters"]
    characters.create_index("id", unique=True, background=True)
    creatures = db_async["creatures"]
    creatures.create_index("id", unique=True, background=True)
    stories = db_async["stories"]
    stories.create_index("id", unique=True, background=True)
except Exception as e:
    print(e)
