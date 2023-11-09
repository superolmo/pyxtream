
from enum import Enum

from jsonschema import exceptions, validate


# class syntax
class SchemaType(Enum):
    SERIES = 1
    SERIES_INFO = 2
    LIVE = 3
    VOD = 4
    CHANNEL = 5
    GROUP = 6

series_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "title": "Series",
    "description": "xtream API Series Schema",
    "type": "object",
    "properties": {
        "seasons": {
            "type": "array",
            "items": {
                "properties": {
                    "air_date": {
                        "type": "string",
                        "format": "date"
                    },
                    "episode_count": { "type": "integer" },
                    "id": { "type": "integer" },
                    "name": { "type": "string" },
                    "overview": { "type": "string" },
                    "season_number": { "type": "integer" },
                    "cover": {
                        "type": "string", 
                        "format": "uri",
                        "qt-uri-protocols": [
                            "http",
                            "https"
                        ]
                    },
                    "cover_big": {
                        "type": "string", 
                        "format": "uri",
                        "qt-uri-protocols": [
                            "http",
                            "https"
                        ]
                    },
                },
                "required": [
                    "id"
                ],
                "title": "Season"
            }
        },
        "info": {
            "properties": {
                "name": { "type": "string" },
                "cover": {
                    "type": "string",
                    "format": "uri",
                    "qt-uri-protocols": [
                        "http",
                        "https"
                    ]
                },
                "plot": { "type": "string" },
                "cast": { "type": "string" },
                "director": { "type": "string" },
                "genre": { "type": "string" },
                "releaseDate": { "type": "string", "format": "date" },
                "last_modified": { "type": "string", "format": "integer" },
                "rating": { "type": "string", "format": "integer" },
                "rating_5based": { "type": "number" },
                "backdrop_path": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "uri",
                        "qt-uri-protocols": [
                            "http",
                            "https"
                        ]
                    }
                },
                "youtube_trailed": { "type": "string" },
                "episode_run_time": { "type": "string", "format": "integer" },
                "category_id": { "type": "string", "format": "integer" }
            },
            "required": [
                "name"
            ],
            "title": "Info"
        },
        "episodes": {
            "patternProperties": {
                "^\d+$": {
                    "type": "array",
                    "items": {
                        "properties": {
                            "id": { "type": "string", "format": "integer" },
                            "episode_num": {"type": "integer" },
                            "title": { "type": "string" },
                            "container_extension": { "type": "string" },
                            "info": {
                                "type": "object",
                                "items": {
                                    "plot": { "type": "string" }
                                }
                            },
                            "customer_sid": { "type": "string" },
                            "added": { "type": "string", "format": "integer" },
                            "season": { "type": "integer" },
                            "direct_source": { "type": "string" }
                        }
                    }
                },
            }
        }
    },
    "required": [
        "info",
        "seasons",
        "episodes"
    ]
}
series_info_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "title": "Series",
    "description": "xtream API Series Info Schema",
    "type": "object",
    "properties": {
        "name": { "type": "string" },
        "cover": {
            "type": "string",
            "format": "uri",
            "qt-uri-protocols": [
                "http",
                "https"
            ]
        },
        "plot": { "type": "string" },
        "cast": { "type": "string" },
        "director": { "type": "string" },
        "genre": { "type": "string" },
        "releaseDate": { "type": "string", "format": "date" },
        "last_modified": { "type": "string", "format": "integer" },
        "rating": { "type": "string", "format": "integer" },
        "rating_5based": { "type": "number" },
        "backdrop_path": {
            "anyOf": [
                {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "uri",
                        "qt-uri-protocols": [
                            "http",
                            "https"
                        ]
                    }
                },
                {"type": "string"}
            ]
        },
        "youtube_trailed": { "type": "string" },
        "episode_run_time": { "type": "string", "format": "integer" },
        "category_id": { "type": "string", "format": "integer" }
    },
    "required": [
        "name",
        "category_id"
    ]
}
live_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "title": "Live",
    "description": "xtream API Live Schema",
    "type": "object",
    "properties": {
        "num": { "type": "integer" },
        "name": { "type": "string" },
        "stream_type": { "type": "string" },
        "stream_id": { "type": "integer" },
        "stream_icon": {
            "anyOf": [
                {
                "type": "string",
                "format": "uri",
                "qt-uri-protocols": [
                    "http",
                    "https"
                ]
                },
                { "type": "null" }
            ]
        },
        "epg_channel_id": {
            "anyOf": [ 
                { "type": "null" },
                { "type": "string" }
            ]
        },
        "added": { "type": "string", "format": "integer" },
        "is_adult": { "type": "string", "format":"number" },
        "category_id": { "type": "string" },
        "custom_sid": { "type": "string" },
        "tv_archive": { "type": "number" },
        "direct_source": { "type": "string" },
        "tv_archive_duration":{
            "anyOf": [
                { "type": "number" },
                { "type": "string", "format": "integer" }
            ]
        }
    }
}
vod_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "title": "VOD",
    "description": "xtream API VOD Schema",
    "type": "object",
    "properties": {
        "num": { "type": "integer" },
        "name": { "type": "string" },
        "stream_type": { "type": "string" },
        "stream_id": { "type": "integer" },
        "stream_icon": {
            "anyOf": [
                {
                "type": "string",
                "format": "uri",
                "qt-uri-protocols": [
                    "http",
                    "https"
                ]
                },
                { "type": "null" }
            ]
        },
        "rating": { 
            "anyOf": [ 
                { "type": "null" },
                { "type": "string", "format": "integer" },
                { "type": "number" }
            ]
        },
        "rating_5based": { "type": "number" },
        "added": { "type": "string", "format": "integer" },
        "is_adult": { "type": "string", "format":"number" },
        "category_id": { "type": "string" },
        "container_extension": { "type": "string" },
        "custom_sid": { "type": "string" },
        "direct_source": { "type": "string" }
    }
}
channel_schema = {}
group_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/product.schema.json",
    "title": "Group",
    "description": "xtream API Group Schema",
    "type": "object",
    "properties": {
        "category_id": { "type": "string" },
        "category_name": { "type": "string" },
        "parent_id": { "type": "integer" }
    }
}

def schemaValidator(jsonData: str, schemaType: SchemaType) -> bool:

    if (schemaType == SchemaType.SERIES):
        json_schema = series_schema
    elif (schemaType == SchemaType.SERIES_INFO):
        json_schema = series_info_schema
    elif (schemaType == SchemaType.LIVE):
        json_schema = live_schema
    elif (schemaType == SchemaType.VOD):
        json_schema = vod_schema
    elif (schemaType == SchemaType.CHANNEL):
        json_schema = channel_schema
    elif (schemaType == SchemaType.GROUP):
        json_schema = group_schema
    else:
        json_schema = "{}"


    try:
        validate(instance=jsonData, schema=json_schema)
    except exceptions.ValidationError as err:
        print(err)
        return False
    return True
