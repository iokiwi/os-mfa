import sys
import os
from argparse import ArgumentParser

from .clouds_configs import *
from .tokens import *


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--os-cloud", help="Specify the name of the cloud configuration you want to use"
    )
    # TODO: Add support for token expiry check and --force option
    # parser.add_argument(
    #     "-f",
    #     "--force",
    #     action="store_true",
    #     help="Force reauthentication even if token hasn't yet expired",
    # )
    args = parser.parse_args()

    os_cloud = args.os_cloud or os.environ.get("OS_CLOUD")

    if os_cloud is None:
        print("OS_CLOUD has not been provided. Run 'os-mfa -h' for more information")
        sys.exit()

    long_term_config_name = "{}-long-term".format(os_cloud)

    config_path = ConfigManager.find_openstack_config_file()
    manager = ConfigManager(config_path)

    if not (
        manager.config_exists(long_term_config_name) or manager.config_exists(os_cloud)
    ):
        print(
            "Neither '{}' or '{}' found in {}".format(
                os_cloud, long_term_config_name, manager.config_path
            )
        )
        sys.exit(1)

    # Create a long-term config if it doesn't exist
    if not manager.config_exists(long_term_config_name):
        print("Creating config: {}".format(long_term_config_name))
        default_config = manager.get_config_by_name(os_cloud)
        long_term_config = create_long_term_config(default_config)
        manager.put_config_by_name(long_term_config_name, long_term_config)

    # Create token based config from long term config
    long_term_config = manager.get_config_by_name(long_term_config_name)
    token_config = get_token_config(long_term_config)
    print("The '{}' config has been updated.".format(os_cloud))
    manager.put_config_by_name(os_cloud, token_config)


if __name__ == "__main__":
    main()
