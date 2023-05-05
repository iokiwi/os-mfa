import os
import platform
import copy

from pathlib import Path

from getpass import getpass
import yaml

from .tokens import *

PASSWORD = None


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
        full_config = self.load_config()
        config = full_config["clouds"].get(name, dict())
        return config


def create_long_term_config(config: dict) -> dict:
    """takes a config and returns a long term config with no secrets"""

    global PASSWORD

    contents = copy.deepcopy(config)

    if "auth_type" in contents:
        del contents["auth_type"]

    if "token" in contents["auth"]:
        del contents["auth"]["token"]

    if "password" in config["auth"]:
        PASSWORD = config["auth"]["password"]
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


# TODO: This method has gotten really unweildy
def get_token_config(config: dict) -> dict:
    """takes a long-term-config and generates a token based config"""

    config = copy.deepcopy(config)

    username = config["auth"].get("username")
    if username is None:
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

    user_domain_name = config["auth"].get("user_domain_name")
    if user_domain_name is None:
        print(
            "Please provide a user_domain_name for user '{}' in project '{}' or press enter to accept the default.".format(
                username, config["auth"].get("project_name")
            )
        )
        user_domain_name = input('User Domain Name ["Default"]: ').strip()

        if user_domain_name == "":
            print('Using default value for user_domain_name: "Default"')
            user_domain_name = "Default"

        config["auth"]["user_domain_name"] = user_domain_name
        print(
            "Specify a value for auth.user_domain_name in the long-term configuration to suppress this prompt in the future."
        )

    print(
        "Authenticating '{}' in project '{}'".format(
            username, config["auth"]["project_name"]
        )
    )

    # Prompt for password unless we already have it from converting to long-term config
    if PASSWORD is None:
        password = getpass(f"Enter Password: ")
    else:
        password = PASSWORD

    totp = input("MFA Code (Press enter to skip): ").strip()
    password = password + totp

    print("Getting token...")
    token = get_token(config["auth"], password)

    token_expiry = isoparse(token["details"]["token"]["expires_at"]).astimezone(
        tz.tzlocal()
    )
    print("Token issued. Expires: {}".format(token_expiry))

    return create_token_config(config, token["token"])
