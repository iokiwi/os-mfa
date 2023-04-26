import json
import os
import sys
import platform
# import logging
# from argparse import ArgumentParser
from getpass import getpass
from pathlib import Path

import yaml
import requests


def get_token(auth: dict, secret: str) -> str:
 
    #   username, password, user_domain_name):
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


# def prompt_password() -> str:
#     return getpass("Password:")


# def prompt_totp() -> str:
#     return input("MFA Temporary Password (Press enter to skip):").strip()


class OpenstackCloudsConfigManager():
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

        search_dirs = [
            current_dir,
            user_dir,
            system_dir
        ]

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
            yaml.dump(content, f)
            self.config = config

    def config_exists(self, name: str) -> bool:
        config = self.load_config()
        return name in config["clouds"]

    def put_config_by_name(self, name: str, config: dict):
        config = self.load_config()
        config["clouds"][name] = config
        self.save_config(config)

    def get_config_by_name(self, name) -> dict:
        config = self.load_config()
        return config["clouds"].get(name, dict())


def create_long_term_config(config: dict) -> dict:
    """ takes a config and returns a long term config with no secrets """

    if "auth_type" in config:
        del config["auth_type"]

    if "token" in config["auth"]:
        del config["auth"]["token"]

    if "password" in config["auth"]:
        del config["auth"]["token"]

    return config

    raise NotImplementedError


def create_ephemeral_config(config: dict) -> dict:
    """ takes a long-term-config and generates a short-lived token based config """

    username = config["auth"].get("username")
    if username is None:
        username = input("Username:").strip()
        # TODO: Offer to save username in -long-term for next time

    password = getpass(f"Password for {username}:")
    totp = input("MFA Temporary Password (Press enter to skip):").strip()
    password = password + totp

    print("Getting token...")
    token = get_token(default_config["auth"], password)

    config["auth_type"] = "token"
    config["auth"]["token"] = token

    for k in ["username", "password", "user_domain_name"]:
        if k in config["auth"]:
            del config["auth"][k]

    return config


if __name__ == "__main__":

    # parser = ArgumentParser()
    # parser.add_argument("--os-cloud")
    # args = parser.parse_args()

    os_cloud = os.environ.get("OS_CLOUD")
    if os_cloud is None:
        sys.exit("$OS_CLOUD must be set in your environment")

    long_term_config_name = "{}-long-term".format(os_cloud)

    config_path = OpenstackCloudsConfigManager.find_openstack_config_file()
    manager = OpenstackCloudsConfigManager(config_path)

    if not (manager.config_exists(long_term_config_name) or manager.config_exists(os_cloud)):
        sys.exit("OS_CLOUD not found", 1)


    if manager.config_exists(long_term_config_name):
        long_term_config = manager.get_config_by_name(long_term_config_name)
        ephemeral_config = create_ephemeral_config(long_term_config)
        manager.put_config_by_name(os_cloud, ephemeral_config)
        sys.exit()

    if manager.config_exists(os_cloud):
        default_config = manager.get_config_by_name(os_cloud)
        long_term_config = create_long_term_config(default_config)
        ephemeral_config = create_ephemeral_config(long_term_config)
        manager.put_config_by_name(os_cloud, ephemeral_config)
        sys.exit()

    sys.exit()
