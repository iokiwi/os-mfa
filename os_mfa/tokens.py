import json

from datetime import datetime
from dateutil.parser import isoparse
from dateutil import tz
from urllib.parse import urlparse

import requests


def utc_to_local(timestamp: datetime) -> datetime:
    local_tz = tz.tzlocal()
    return timestamp.astimezone(local_tz)


def get_token(auth: dict, secret: str) -> str:
    # Ensure URL is in consistent format.
    # NOTE: v3 is probably an okayish assumption but technically we shouldn't assume
    parsed_url = urlparse(auth["auth_url"])
    url = "{}://{}/{}".format(parsed_url.scheme, parsed_url.netloc, "v3/auth/tokens")

    r = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "auth": {
                    "identity": {
                        "methods": ["password"],
                        "password": {
                            "user": {
                                "name": auth["username"],
                                "domain": {"name": auth["user_domain_name"]},
                                "password": secret,
                            }
                        },
                    },
                    "scope": {"project": {"id": auth["project_id"]}},
                }
            }
        ),
    )

    if not r.ok:
        print(r.text())

    return {"token": r.headers.get("x-subject-token"), "details": r.json()}
