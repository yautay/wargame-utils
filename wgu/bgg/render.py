"""CLI serialization; source content and verification are separate JSON fields."""
import json


def result(data):
    return json.dumps(dict(source='BoardGameGeek', source_url='https://boardgamegeek.com/',
                           data=data), ensure_ascii=False, indent=2)
