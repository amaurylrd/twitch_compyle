from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from compyle.settings import MONGO_DB
from compyle.utils.types import Singleton


class MongoDB(metaclass=Singleton):
    def __init__(self):
        client = MongoClient(MONGO_DB["client_uri"])
        database: Database = client.get_default_database()
        collection: Collection = database.create_collection("clips")
        test = {"test": "test"}
        collection.insert_many([test])
