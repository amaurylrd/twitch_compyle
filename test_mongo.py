import os

import pytest

import compyle.settings as settings
from compyle.services.databases.mongo import MongoDB

# x = {
#     "type": "object",
#     "properties": {
#         "id": {"type": "string"},
#         "url": {"type": "string"},
#         "embed_url": {"type": "string"},
#         "broadcaster_id": {"type": "string"},
#     },
#     "anyOf": [
#         {"required": ["id"]},
#         {"required": ["url"]},
#         {"required": ["embed_url"]},
#         {"required": ["broadcaster_id"]},
#     ],
#     "additionalProperties": False,
# }
# # https://www.mongodb.com/basics/json-schema-examples
# schema = {
#     "$schema": "https://json-schema.org/draft/2020-12/schema",
#     "$id": "https://example.com/product.schema.json",
#     "title": "Record of Employee",
#     "description": "This document records the details of an employee",
#     "type": "object",
# }
#    import json
# print(json.dumps(x, indent=4))
#     print(json.dumps(schema, indent=4))


if __name__ == "__main__":
    mongo = MongoDB()
    json = {"test1": "test"}
    collection = "clips"
    mongo.insert_document(collection, json)
