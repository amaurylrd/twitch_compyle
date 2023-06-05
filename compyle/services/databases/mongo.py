import logging
from collections import OrderedDict
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Union


from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import (
    DeleteResult,
    InsertManyResult,
    InsertOneResult,
    UpdateResult,
)
from pymongo.server_api import ServerApi, ServerApiVersion
from retrying import retry

from compyle.settings import MONGO_CONFIG
from compyle.utils.types import Singleton

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


def log_before_after(func):
    @wraps(func)
    def _wrapper(self, collection: str, subject: Union[dict, List[dict]], *args, **kwargs):
        keys = OrderedDict([("db", self.database.name), ("collection", collection)])

        # TODO afficher les arguments
        # if isinstance(subject, list):
        #     keys.move_to_end(("documents", [document.get("_id", None) for document in subject]))
        # elif "_id" in subject:  # todo marche pas pour get_document
        #     keys.move_to_end(("document", subject["_id"]))
        # else:
        #     keys.move_to_end(("query", subject))
        #     keys.move_to_end(("projection", kwargs.get("projection", None)))

        LOGGER.debug("Before %s [%s]", func.__name__, ", ".join(f"{key}={value}" for key, value in keys.items()))
        result = func(self, collection, subject, *args, **kwargs)
        LOGGER.debug(
            "After %s [result_successful=%s]",
            func.__name__,
            result.matched_count > 0 if isinstance(result, UpdateResult) else result.acknowledged,
        )

        return result

    return _wrapper


class MongoDB(metaclass=Singleton):
    def __init__(self):
        self.__connect()

    @retry(stop_max_attempt_number=30, wait_fixed=2000, stop_max_delay=60000)
    def __connect(self, timeout: int = 4000, version: ServerApiVersion = ServerApiVersion.V1):
        """Connects to the MongoDB database."""
        self.client = MongoClient(
            MONGO_CONFIG.client_uri, serverSelectionTimeoutMS=timeout, server_api=ServerApi(version, strict=True)
        )
        LOGGER.debug("Connection information [host=%s, port=%s]", self.client.HOST, self.client.PORT)

        self.database: Database = self.client[MONGO_CONFIG.client_name]
        LOGGER.debug("Connected to MongoDB database '%s'", self.database.name)

    def __getitem__(self, item: str) -> Collection:
        """Gets the specified collection from the database.

        Args:
            item (str): the name of the collection.

        Returns:
            Collection: the specified collection.
        """
        return self.client[item]

    def __normalize_document(self, document: dict) -> dict:
        document["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        if "created_at" not in document:
            document["created_at"] = document["updated_at"]

        return document

    @log_before_after
    def insert_document(self, collection: str, document: dict) -> InsertOneResult:
        return self.database[collection].insert_one(self.__normalize_document(document))

    @log_before_after
    def insert_documents(self, collection: str, documents: List[dict]) -> InsertManyResult:
        return self.database[collection].insert_many(self.__normalize_document(document) for document in documents)

    @log_before_after
    def update_document(self, collection: str, document: dict) -> UpdateResult:
        return self.database[collection].update_one(
            {"_id": document["_id"]}, {"$set": self.__normalize_document(document)}
        )

    @log_before_after
    def delete_document(self, collection: str, document: dict) -> DeleteResult:
        return self.database[collection].delete_one({"_id": document["_id"]})

    @log_before_after
    def get_document(self, collection: str, query: Dict[str, Any]) -> Optional[Any]:
        """Retrieves the document with the specified id from the specified collection.

        Example:
            >>> document = self.get_document("clips", {"_id": "5f9e1b7b9b9b9b9b9b9b9b9b"})

        Args:
            collection (str): the name of the collection.
            query (Dict[str, Any]): the filter query to retrieve the document.

        Returns:
            Optional[Any]: the document if any, otherwise `None`.
        """
        return self.database[collection].find_one({"_id": query["_id"]})

    # pylint: disable=line-too-long
    @log_before_after
    def get_documents(
        self,
        collection: str,
        query: dict,
        projection=None,
        limit=0,
        offset=0,
        sorts_list=None,
        batch_size=100,
    ) -> list:
        """Queries documents from the specified collection with the specified filter parameters.

        Args:
            collection (str): the name of the collection.
            query (dict): the query to filter the documents.
            projection (Dict[str, str], optional): containes fields be to to excluded from the result. Defaults to None.
            limit (int, optional): the maximum number of results to return. Defaults to 0 (no limit).
            offset (int, optional): the number of documents to omit (from the start of the result set).
            sorts_list (Dict[str, str], optional): the list of (key, direction) pairs specifying the sort order. Defaults to None.
            batch_size (int, optional): the . Defaults to 100.

        Returns:
            list: _description_
        """
        # query example = {"name": "John", "age": {"$gt": 18}}
        # projection example = {"_id": False}
        # LOGGER.debug(
        #     "get_documents [db=%s, collection=%s, query=%s, projection=%s]",
        #     self.database.name,
        #     collection,
        #     query,
        #     projection,
        # )

        cursor = self.database[collection].find(
            filter=query, projection=projection, skip=offset, limit=limit, sort=sorts_list, batch_size=batch_size
        )

        return list(cursor)

    # self.client.create_database("compyle")

    # collection: Collection = database.create_collection("clips")
    # test = {"test": "test"}
    # collection.insert_many([test])
