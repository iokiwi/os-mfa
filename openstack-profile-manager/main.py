import os
import sys
import json
import platform
import logging

from argparse import ArgumentParser
from getpass import getpass
from pathlib import Path

import yaml
import requests

def find_openstack_config_file() -> Path:

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

def load_config(path: Path) -> dict:
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    return config


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
        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)
            return self.config

    # def write_config_file(self, config) -> dict:
    #     pass

    def config_exists(self, name: str) -> bool:
        pass

    def put_config_by_name(self, name: str, config: dict):
        pass

    def get_config_by_name(self, name) -> dict:
        config = self.read_config_file()

        return self.config["clouds"]
        pass


if __name__ == "__main__":

    # parser = ArgumentParser()
    # parser.add_argument("--os-cloud")
    # args = parser.parse_args()

    os_cloud_config_name = os.environ.get("OS_CLOUD")
    if os_cloud_config_name is None:
        sys.exit("$OS_CLOUD must be set in your environment")

    long_term_config_name = "{}-long-term".format(os_cloud_config_name)

    config_path = OpenstackCloudsConfigManager.find_openstack_config_file()
    manager = OpenstackCloudsConfigManager(config_path)

    default_config = manager.load_config_by_name(os_cloud_config_name)
    long_term_config = manager.load_config_by_name(long_term_config_name)

    if manager.config_exists(long_term_config_name):
        pass
        # Create ephemeral config
        # return
    elif manager.config_exists(os_cloud_config_name):
        pass
        # Create long term config
        # Get long term config
        # Create ephemeral config
        


    long_term_config = manager.load_config_by_name(long_term_config_name)

    # if


    print(config_path)

    sys.exit()

    # Part 1: Look for clouds.yaml or static-clouds.yaml
    try:
        config_path = find_config_path("static-clouds.yaml")
    except FileNotFoundError:

        print("static-clouds.yaml not found")

        config_path = find_config_path("clouds.yaml")

        # Dump clouds.yaml into static-clouds.yaml
        with open(config_path / "clouds.yaml", "r") as f1:
            content = yaml.safe_load(f1)

            if "auth_type" in content["clouds"][os_cloud]:
                del content["clouds"][os_cloud]["auth_type"]

            if "token" in content["clouds"][os_cloud]["auth"]:
                del content["clouds"][os_cloud]["auth"]["token"]

            with open(config_path / "static-clouds.yaml", "w") as f2:
                print("Creating", config_path / "static-clouds.yaml")
                yaml.dump(content, f2)

    # Part 2: Get token
    config = load_config(config_path / "static-clouds.yaml")

    cloud_config = config["clouds"][os_cloud]

    user_domain_name = cloud_config["auth"].get("user_domain_name", "Default")
    project_id = cloud_config["auth"]["project_id"]
    auth_url = cloud_config["auth"]["auth_url"]

    username = cloud_config["auth"].get("username")
    if username is None:
        username = input("Username:").strip()
        # TODO: Offer to save username in static-config.yml for next time

    password = cloud_config["auth"].get("password")
    if password is None:
        password = getpass(f"Password for {username}:")
    else:
        # TODO: Suggest/offer to delete password from static-config.yml
        pass

    totp = input("MFA Temporary Password (Press enter to skip):").strip()
    password = password + totp

    print("Getting token...")
    token = get_token(username, password, user_domain_name)

    # Part 3: Update clouds.yaml file
    if not os.path.exists(config_path / "clouds.yaml"):
        ephemeral_config = load_config(config_path / "static-clouds.yaml")
        with open(config_path / "clouds.yaml", "w") as f:
            pass
    else:
        ephemeral_config = load_config(config_path / "clouds.yaml")

    # set auth_type = token
    ephemeral_config["clouds"][os_cloud]["auth_type"] = "token"

    # set token
    auth = ephemeral_config["clouds"][os_cloud]["auth"]
    auth["token"] = token

    # Clear unwanted auth attributes
    for x in ["username", "password", "user_domain_name"]:
        if x in auth:
            del auth[x]
    ephemeral_config["clouds"][os_cloud]["auth"] = auth

    # Write modified config to clouds.yaml
    print("Updating", config_path / "clouds.yaml")
    with open(config_path / "clouds.yaml", "w") as f:
        yaml.dump(ephemeral_config, f)