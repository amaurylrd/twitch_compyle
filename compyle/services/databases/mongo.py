from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from compyle.settings import MONGO_DB
from compyle.utils.types import Singleton


class MongoDB(metaclass=Singleton):
    def __init__(self):
        self.client = MongoClient(MONGO_DB["client_uri"])
        self.database: Database = self.client[MONGO_DB["client_name"]]
        print(self.database)
        self.database["test1"].insert_one({"test": 10})

    # def insert_one(self, collection: str, document: dict):
    #     print("ok")
    #     print(collection in self.database.list_collection_names())
    #     self.database[collection].insert_one(document)

    # def insert_many(self, collection: str, documents: list):
    #     self.database[collection].insert_many(documents)

    # self.client.create_database("compyle")

    # collection: Collection = database.create_collection("clips")
    # test = {"test": "test"}
    # collection.insert_many([test])
