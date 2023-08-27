import copy
from pathlib import Path
from getpass import getpass

import yaml


from openstack.config.loader import OpenStackConfig

from .tokens import get_token, Token

from typing import Dict, List, Any


class Config:
    def __init__(self, name: str, properties: Dict[str, Any]):
        self.name = name
        self.properties = properties


class ConfigFileManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None

    @classmethod
    def get_config_dirs(cls) -> List[Path]:
        osc = OpenStackConfig()
        return [
            Path(path)
            for path in osc._config_files
            if path.endswith("yaml") or path.endswith("yml")
        ]

    @classmethod
    def find_openstack_config_file(cls) -> Path:
        """Find the clouds.yaml file

        :returns: Path to clouds.yaml
        :throws: FileNotFoundError
        """

        search_paths = ConfigFileManager.get_config_dirs()
        for f in search_paths:
            if f.exists():
                return f
        raise FileNotFoundError("Could not find a clouds.yml or clouds.yaml")

    def load_config(self) -> Dict[str, Any]:
        if self.config is not None:
            return self.config

        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)
            return self.config

    def save_config(self, config: Dict[str, Any]):
        with open(self.config_path, "w") as f:
            yaml.dump(config, f)
            self.config = config

    def config_exists(self, name: str) -> bool:
        config = self.load_config()
        return name in config["clouds"]

    def put_config_by_name(self, name: str, config: Config) -> bool:
        full_config = self.load_config()
        full_config["clouds"][name] = config.properties
        self.save_config(full_config)
        return True

    def get_config_by_name(self, name: str) -> Config:
        """ Returns a config by name
            :throws: KeyError if config is not found
        """
        full_config = self.load_config()
        properties = full_config["clouds"][name]
        return Config(name, properties)


def get_sanitized_config(config: Config) -> Config:
    """Takes a config and returns a sanitized config without secrets"""

    sanitized_config = copy.deepcopy(config)

    if "auth_type" in sanitized_config.properties:
        del sanitized_config.properties["auth_type"]

    if "token" in sanitized_config.properties["auth"]:
        del sanitized_config.properties["auth"]["token"]

    if "password" in sanitized_config.properties["auth"]:
        del sanitized_config.properties["auth"]["password"]

    return sanitized_config


def create_token_config(config: Config, token: Token) -> Config:
    token_config = copy.deepcopy(config)

    token_config.properties["auth_type"] = "token"
    token_config.properties["auth"]["token"] = token.value

    for k in ["username", "password", "user_domain_name"]:
        if k in token_config.properties["auth"]:
            del token_config.properties["auth"][k]

    return token_config


def prompt_username(config: Config) -> str:
    auth = config.properties["auth"]
    print("Please enter your username for project '{}'".format(auth["project_name"]))
    username = input("Username: ").strip()
    print(
        "Specify a value for {}.auth.username in your clouds.yaml "
        "to suppress this prompt in the future.".format(config.name)
    )
    return username


def prompt_user_domain_name(config: Config) -> str:
    message = (
        "Please provide a user_domain_name for user '{}' in "
        "project '{}' or press enter to accept the default."
    )
    print(
        message.format(
            config.properties["auth"].get("username"),
            config.properties["auth"].get("project_name"),
        )
    )
    user_domain_name = input('User Domain Name ["Default"]: ').strip()
    if user_domain_name == "":
        print('Using default value for user_domain_name: "Default"')
        user_domain_name = "Default"
    print(
        "Specify a value for {}.auth.user_domain_name in the long-term"
        "configuration to suppress this prompt in the future.".format(config.name)
    )
    return user_domain_name


def prompt_password(config: Config) -> str:
    auth = config.properties["auth"]
    print(
        "Authenticating '{}' in project '{}'".format(
            auth["username"], auth["project_name"]
        )
    )
    return getpass("Enter Password: ")


def get_token_config(config: Config) -> Config:
    """Takes a long-term-config and generates a token based config"""

    config = copy.deepcopy(config)

    username = config.properties["auth"].get("username")
    if username is None:
        username = prompt_username(config)
    config.properties["auth"]["username"] = username

    user_domain_name = config.properties["auth"].get("user_domain_name")
    if user_domain_name is None:
        user_domain_name = prompt_user_domain_name(config)
        config.properties["auth"]["user_domain_name"] = user_domain_name

    password = prompt_password(config)
    totp = input("MFA Code (Press enter to skip): ").strip()
    auth_secret = password + totp

    print("Getting token...")
    token = get_token(config.properties["auth"], auth_secret)

    print("Token issued. Expires: {}".format(token.expires_at))

    return create_token_config(config, token)
