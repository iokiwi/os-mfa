import os
import platform
import json
import sys
import copy

import yaml

from pathlib import Path

from getpass import getpass

import requests


class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = dict()

    @classmethod
    def find_openstack_config_file(cls) -> Path:
        current_dir = Path.cwd()
        user_home = Path.home()
        user_dir = user_home / ".config" / "openstack"

        if platform.system() == "Windows":
            system_dir = Path("C:/ProgramData/openstack")
        else:
            system_dir = Path("/etc/openstack")

        search_dirs = [current_dir, user_dir, system_dir]

        override_dir = os.environ.get("OS_CLIENT_CONFIG_FILE")
        if override_dir:
            search_dirs.insert(0, override_dir)

        for search_dir in search_dirs:
            for filename in ["clouds.yml", "clouds.yaml"]:
                p = search_dir / filename
                if p.exists():
                    return p

        raise FileNotFoundError("Could not find a clouds.yml or clouds.yaml")

    def load_config(self) -> dict:
        if self.config:
            return self.config

        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)
            return self.config

    def save_config(self, config):
        with open(self.config_path, "w") as f:
            yaml.dump(config, f)
            self.config = config

    def config_exists(self, name: str) -> bool:
        config = self.load_config()
        return name in config["clouds"]

    def put_config_by_name(self, name: str, config: dict):
        full_config = self.load_config()
        full_config["clouds"][name] = config
        self.save_config(full_config)

    def get_config_by_name(self, name) -> dict:
        config = self.load_config()
        cloud = config["clouds"].get(name, dict())
        return cloud


def get_token(auth: dict, secret: str) -> str:
    # Note: we shouldn't assume v3
    url = "{}/{}".format(auth["auth_url"], "/v3/auth/tokens")
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
    return r.headers.get("x-subject-token")


def create_long_term_config(config: dict) -> dict:
    """takes a config and returns a long term config with no secrets"""

    config = copy.deepcopy(config)

    # username = config["auth"].get("username")
    # if username is None:
    #     save = input("Would you like to save your username? [Y/n]").strip()
    #     if save == "" or save.lower().startswith("y"):
    #         username = input("Username:").strip()
    #         config["auth"]["username"]

    if "auth_type" in config:
        del config["auth_type"]

    if "token" in config["auth"]:
        del config["auth"]["token"]

    if "password" in config["auth"]:
        del config["auth"]["password"]

    return config


def create_token_config(long_term_config: dict, token: str) -> dict:
    token_config = copy.deepcopy(long_term_config)

    token_config["auth_type"] = "token"
    token_config["auth"]["token"] = token

    for k in ["username", "password", "user_domain_name"]:
        if k in token_config["auth"]:
            del token_config["auth"][k]

    return token_config


def get_token_config(config: dict) -> dict:
    """takes a long-term-config and generates a token based config"""

    config = copy.deepcopy(config)

    username = config["auth"].get("username")
    if username is None:
        username = input("Username:").strip()
        # save = input("Would you like to save your username for next time? [y/N]: ").strip()
        # if save == "" or save.lower().startswith("y"):
        #     # Do something
        #     pass

    password = getpass(f"Password for {username}:")
    totp = input("MFA Temporary Password (Press enter to skip):").strip()
    password = password + totp

    print("Getting token...")
    token = get_token(config["auth"], password)
    return create_token_config(config, token)
