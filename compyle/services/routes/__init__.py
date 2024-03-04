import json
import logging
import os

import jsonschema

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

__all__ = []
dirname = os.path.join(os.path.dirname(__file__))
schema = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "object",
            "required": ["base_url", "slug"],
            "properties": {
                "base_url": {
                    "type": "string",
                },
                "slug": {
                    "type": "string",
                },
                "req": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                    },
                },
                "opt": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                    },
                },
            },
            "additionalProperties": False,
        }
    },
}

for fname in os.listdir(dirname):
    fpath = os.path.join(dirname, fname)

    if os.path.isfile(fpath) and fpath.endswith(".json"):
        fname = fname[:-5]

        try:
            with open(fpath, encoding="utf-8") as fp:
                try:
                    fcontent = json.load(fp)
                    jsonschema.validate(fcontent, schema)
                    globals()[fname] = fcontent
                    __all__.append(fname)
                except (NameError, json.JSONDecodeError, jsonschema.ValidationError) as e:
                    LOGGER.warn("Invalid JSON instance (%s) %s", fpath, e.args[0])
                except jsonschema.SchemaError as e:
                    LOGGER.warn("Invalid JSON schema (%s) %s", fpath, e.args[0])
        except OSError as e:
            LOGGER.warn("Failed to open file: %s", fpath)
