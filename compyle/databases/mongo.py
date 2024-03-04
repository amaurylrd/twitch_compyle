import logging
from collections import OrderedDict
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

from pymongo import ASCENDING, MongoClient
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
        """Connects to the MongoDB database. Retries 30 times with a 2 seconds delay between each try.

        Args:
            timeout (int, optional): the timeout in milliseconds. Defaults to 4000.
            version (ServerApiVersion, optional): the version of the server API. Defaults to ServerApiVersion.V1.
        """
        self.client = MongoClient(
            MONGO_CONFIG.client_uri, serverSelectionTimeoutMS=timeout, server_api=ServerApi(version, strict=True)
        )
        LOGGER.debug(
            "Connection information [host=%s, port=%s, version=%s]", self.client.HOST, self.client.PORT, version
        )

        self.database: Database = self.client[MONGO_CONFIG.client_name]
        LOGGER.info("Connected to MongoDB database '%s'", self.database.name)

    def __disconnect(self):
        """Disconnects from the MongoDB database."""
        if self.client:
            self.client.close()
            LOGGER.info("Disconnected from MongoDB database '%s'", self.database.name)

    def __enter__(self) -> "MongoDB":
        """Connects to the MongoDB database and returns the instance.

        Returns:
            MongoDB: the instance of the MongoDB database.
        """
        if not self.client:
            self.__connect()
        return self

    # pylint: disable=line-too-long,unused-argument
    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """Disconnects from the MongoDB database. If the context was exited without an exception, all three arguments will be None.

        Args:
            exc_type (Any): the type of the exception.
            exc_val (Any): the value of the exception.
            exc_tb (Any): the traceback of the exception.
        """
        self.__disconnect()

    def __getitem__(self, item: str) -> Collection:
        """Gets the specified collection from the database.

        Args:
            item (str): the name of the collection.

        Returns:
            Collection: the specified collection.
        """
        return self.client[item]

    def __normalize_document(self, document: dict) -> dict:
        """Timestamps the document if necessary to keep track of creation and update date.

        Args:
            document (dict): the document to normalize.

        Returns:
            dict: the normalized document.
        """
        document["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
        if "inserted_at" not in document:
            document["inserted_at"] = document["updated_at"]

        return document

    @log_before_after
    def insert_document(self, collection: str, document: dict) -> InsertOneResult:
        """Inserts the specified document into the specified collection.

        Args:
            collection (str): the name of the collection. If the collection does not exist, it is created.
            document (dict): the document to insert.

        Returns:
            InsertOneResult: the result of the insertion.
        """
        return self.database[collection].insert_one(self.__normalize_document(document))

    @log_before_after
    def insert_documents(self, collection: str, documents: List[dict]) -> InsertManyResult:
        """Inserts the specified list of documents into the specified collection.

        Args:
            collection (str): the name of the collection. If the collection does not exist, it is created.
            documents (List[dict]): the list of documents to insert.

        Returns:
            InsertManyResult: the result of the many insertions.
        """
        return self.database[collection].insert_many(self.__normalize_document(document) for document in documents)

    @log_before_after
    def update_document(self, collection: str, document: dict) -> UpdateResult:
        """Updates the specified document in the specified collection.

        Args:
            collection (str): the name of the collection. If the collection does not exist, it is created.
            document (dict): the document to update. Must contain the _id field.

        Returns:
            UpdateResult: the result of the update.
        """
        return self.database[collection].update_one(
            {"_id": document["_id"]}, {"$set": self.__normalize_document(document)}
        )

    @log_before_after
    def delete_document(self, collection: str, document: dict) -> DeleteResult:
        """Deletes the specified document from the specified collection.

        Args:
            collection (str): the name of the collection. If the collection does not exist, it is created.
            document (dict): the document to delete. Must contain the _id field.

        Returns:
            DeleteResult: the result of the deletion.
        """
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

    # @log_before_after
    def get_documents(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]],
    ) -> List[Any]:
        """Retrieves the documents from the specified collection.

        Args:
            collection (str): the name of the collection.
            pipeline (List[Dict[str, Any]]): the MongoDB query pipeline.

        Returns:
            List[Any]: the list of documents.
        """
        return list(self.database[collection].aggregate(pipeline, allowDiskUse=True))

    # pylint: disable=too-many-arguments, line-too-long
    @classmethod
    def build_pipeline(
        cls,
        match: Dict[str, Any],
        *args,
        project: Optional[Dict[str, Any]] = None,
        group: Optional[Dict[str, Any]] = None,
        sort: Optional[Union[str, List[Tuple[str, int]]]] = None,
        offset: int = 0,
        limit: int = 0,
        unwind: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Builds a MongoDB query pipeline.

        See:
            https://docs.mongodb.com/manual/reference/operator/aggregation-pipeline/

        Args:
            match (Dict[str, Any]): Filters the documents to pass only the documents that match the specified condition.
            *args: additional arguments to add to the pipeline, see https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/feature-support-42.
            project (Optional[Dict[str, Any]], optional): transforms the documents to a new form by adding, removing, or updating fields. Defaults to None.
            group (Optional[Dict[str, Any]], optional): groups documents by one or more fields and performs various aggregate functions on the grouped data.. Defaults to None.
            sort (Optional[Union[str, List[Tuple[str, int]]]], optional): sorts the documents based on the specified fields.. Defaults to None.
            offset (int, optional): skips the specified number of documents. Defaults to None.
            limit (int, optional): limits the number of documents passed to the next stage. Defaults to 0.
            unwind (Optional[str], optional): deconstructs an array field from the input documents to output a document for each element. Defaults to None.

        Returns:
            _Pipeline: the MongoDB query pipeline.
        """
        pipeline: Dict[str, Any] = {"$match": match, "$skip": offset}

        if limit > 0:
            pipeline["$limit"] = limit

        if sort:
            if isinstance(sort, str):
                pipeline["$sort"] = {sort: ASCENDING}
            else:
                pipeline["$sort"] = OrderedDict(sort)

        if group:
            pipeline["$group"] = group

        if project:
            pipeline["$project"] = project

        if unwind:
            pipeline["$unwind"] = unwind

        return [{k: v} for k, v in pipeline.items()] + list(args)
