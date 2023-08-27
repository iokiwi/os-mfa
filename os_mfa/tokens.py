import json
from urllib.parse import urlparse
import requests
from datetime import datetime, tzinfo

from dateutil import tz
from dateutil.parser import isoparse

from typing import Dict, Any, Optional


class Token:
    def __init__(self, value, expires_at: str, issued_at: Optional[str] = None) -> None:
        self.value = value
        self.expires_at = isoparse(expires_at)

        if issued_at is not None:
            self.issued_at = isoparse(issued_at)

    def get_expiry(self, timezone: Optional[tzinfo] = None) -> datetime:
        if timezone is None:
            timezone = tz.tzlocal()
        return self.expires_at.astimezone(timezone)

    def is_expired(self):
        if self.get_expiry() < datetime.now():
            return False
        return True


def get_token_url(auth_url: str) -> str:
    parsed_url = urlparse(auth_url)
    return "{}://{}/{}".format(parsed_url.scheme, parsed_url.netloc, "v3/auth/tokens")


def construct_token_request_body(auth: Dict[str, Any], secret: str) -> Dict[str, dict]:
    """
    throws: KeyError
    """
    return {
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


def get_token(auth: Dict[str, Any], secret: str) -> Token:
    """Get a token from the OpenStack Identity API.

    :returns:
    :throws: requests.exceptions.HTTPError
    """

    url = get_token_url(auth["auth_url"])
    body = construct_token_request_body(auth, secret)

    print(body)

    r = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(body),
    )
    r.raise_for_status()

    token = r.headers["x-subject-token"]
    token_details = r.json()["token"]

    return Token(
        token,
        token_details["expires_at"],
        #  token_details["issued_at"]
    )
