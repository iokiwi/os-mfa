import copy
from pathlib import Path
from getpass import getpass

import yaml
from dateutil import tz
from openstack.config.loader import OpenStackConfig

from .tokens import *


class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = dict()

    @classmethod
    def get_config_dirs(cls) -> list:
        osc = OpenStackConfig()
        return [path for path in osc._config_files if path.endswith("yaml") or path.endswith("yml")]

    @classmethod
    def find_openstack_config_file(cls) -> Path:
        search_paths = ConfigManager.get_config_dirs()
        for f in search_paths:
            if Path(f).exists():
                return f
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
        full_config = self.load_config()
        config = full_config["clouds"].get(name, dict())
        return config


def create_long_term_config(config: dict) -> dict:
    """takes a config and returns a long term config with no secrets"""

    password = None
    long_term_config = copy.deepcopy(config)

    if "auth_type" in long_term_config:
        del long_term_config["auth_type"]

    if "token" in long_term_config["auth"]:
        del long_term_config["auth"]["token"]

    if "password" in long_term_config["auth"]:
        password = long_term_config["auth"]["password"]
        del long_term_config["auth"]["password"]

    return (long_term_config, password)


def create_token_config(long_term_config: dict, token: str) -> dict:
    token_config = copy.deepcopy(long_term_config)

    token_config["auth_type"] = "token"
    token_config["auth"]["token"] = token

    for k in ["username", "password", "user_domain_name"]:
        if k in token_config["auth"]:
            del token_config["auth"][k]

    return token_config


def prompt_username(config) -> str:
    print(
        "Please enter your username for project '{}'".format(
            config["auth"]["project_name"]
        )
    )
    username = input("Username: ").strip()
    config["auth"]["username"] = username
    print(
        "Specify a value for auth.username in the long-term configuration to suppress this prompt in the future."
    )


def prompt_user_domain_name(config) -> str:
    print(
        "Please provide a user_domain_name for user '{}' in project '{}' or press enter to accept the default.".format(
            config["auth"].get("username"), config["auth"].get("project_name")
        )
    )
    user_domain_name = input('User Domain Name ["Default"]: ').strip()
    if user_domain_name == "":
        print('Using default value for user_domain_name: "Default"')
        user_domain_name = "Default"
    print(
        "Specify a value for auth.user_domain_name in the long-term configuration to suppress this prompt in the future."
    )
    return user_domain_name


def prompt_password(config):
    print(
        "Authenticating '{}' in project '{}'".format(
            config["auth"]["username"], config["auth"]["project_name"]
        )
    )
    return getpass(f"Enter Password: ")


# TODO: This method has gotten really unwieldy
def get_token_config(config: dict, password=None) -> dict:
    """takes a long-term-config and generates a token based config"""

    config = copy.deepcopy(config)

    username = config["auth"].get("username")
    if username is None:
        username = prompt_username(config)
    config["auth"]["username"] = username

    user_domain_name = config["auth"].get("user_domain_name")
    if user_domain_name is None:
        user_domain_name = prompt_user_domain_name(config)
        config["auth"]["user_domain_name"] = user_domain_name

    if password is None:
        password = prompt_password(config)

    totp = input("MFA Code (Press enter to skip): ").strip()
    auth_secret = password + totp

    print("Getting token...")
    token = get_token(config, auth_secret)

    token_expiry = parse_token_expiry(token["details"]["token"]).astimezone(
        tz.tzlocal()
    )

    print("Token issued. Expires: {}".format(token_expiry))
    token = get_token(config, auth_secret)
    return create_token_config(config, token["token"])
