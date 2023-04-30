# OS-MFA: Easily manage one or more openstack credentials for command line and programmatic access

os-mfa makes using MFA with cli/programmatic authentication with OpenStack easier and more secure by combining the convenience of durable authentication session persistence with better credential management hygiene though automatically managing the lifecycle of authentication tokens in the `clouds.yaml` file.

Inspired by https://github.com/broamski/aws-mfa

Note: This is currently a proof of concept/Work in progress. Pull requests welcome.

## In this README

* [The Problems this project aims to Address](#the-problems-this-project-aims-to-address)
* [Installation](#installation)
  * [Linux](#linux)
  * [macOS](#macos)
  * [Windows](#windows)
* [Quick Start](#quick-start)
* [How it Works](#how-it-works)

## The Problem(s) this project aims to address

Openstack provides several methods for configuring authentication for its SDK's and clients including CLI arguments, environment variables and a [clouds.yaml](https://docs.openstack.org/python-openstackclient/latest/configuration/index.html#configuration-files) file.

### 1. Using openrc files/environment variables is not durable across terminal sessions

For some reason the preferred / default authentication method users are steered towards is using openrc files - non-trivial bash files which set environment variables in your shell session.

Using environment variables to persist your authentication session is not durable across terminal instances or restarts. If you open a new terminal for any reason you will need to re authenticate there with your username, password and MFA token. This becomes very tiresome very quickly.

### 2. Using clouds.yaml does not work nicely with token authentication or MFA

Openstack does provide a better, more persisted, authentication mechanism by way of the [clouds.yaml](https://docs.openstack.org/python-openstackclient/latest/configuration/index.html#configuration-files) configuration file.

Switching sessions is then simplified by referencing the cloud config name from `clouds.yaml
  * Using an cli argument (`--os-cloud=<name>`) 
  * Setting the `OS_CLOUD` environment variable inline (E.g `OS_CLOUD=<name> <command>`)
  * Exporting `OS_CLOUD` environnement variable to used by all future commands in that session (`export OS_CLOUD=<name>`)

However using `clouds.yaml` files also has some drawbacks.

* It discourages token based authorization as tokens expire after 12 hours requiring users to constantly manually update clouds.yaml with new tokens.
* It discourages the use of MFA which requires token based authorization.
* It encourages storing usernames and passwords in clear text in a file on your machine as this is less friction than using token based authorization.

## Best of both worlds: Convenience + Hygiene with os-mfa

This openstack MFA helper combines the convenience of durable authentication session persistence with better security hygiene by utilizing `clouds.yaml` and automatically managing the lifecycle of tokens in the config file allowing users to keep passwords out of their `clouds.yaml` file.

## Quick Start

1. Obtain a `clouds.yaml` file from the cloud dashboard. For catalyst cloud:
    * Go to https://dashboard.cloud.catalyst.net.nz/project/api_access/
    * Hover over `Download OpenStack RC File` on the top right
    * Click the `OpenStack clouds.yml file`

2. Place your `clouds.yaml` file in one of the following locations detailed in the [upstream docs](https://docs.openstack.org/python-openstackclient/latest/cli/man/openstack.html#config-files)
    * `./clouds.yaml`
    * `~/config/openstack/clouds.yaml`
    * `/etc/openstack/clouds.yaml`

3. E.g. Assign and export your config name as the OS_CLOUD environment variable

    ```bash
    $ export OS_CLOUD=catalystcloud
    ```

4. Authenticate using `os-mfa`

    ```bash
    $ os-mfa

    Authenticating 'john.smith@example.com' in project 'john-smith'
    Enter Password:
    TOTP (press enter to skip): 654321
    ```

5. Happy OpenStacking
    ```bash
    $ openstack server list
    +---------------+---------------+--------+---------------+---------------+---------+
    | ID            | Name          | Status | Networks      | Image         | Flavor  |
    +---------------+---------------+--------+---------------+---------------+---------+
    | a5d3814a-4f6e | proxy-server- | ACTIVE | proxy-        | N/A (booted   | c1.c1r1 |
    | -493f-aa03-ac | yohjuqh5vzhm  |        | network-lju2p | from volume)  |         |
    | 13fdb9a860    |               |        | kokjtsh=10.0. |               |         |
    |               |               |        | 0.4, 103.***. |               |         |
    |               |               |        | ***.***       |               |         |
    +---------------+---------------+--------+---------------+---------------+---------+
    ```
## How it works

With os-mfa we introduce the concept of a "Long Term" configuration, distinguished by a suffix of `-long-term`, which is a copy of the original config that does not contain any secretes such as passwords or tokens.

os-mfa will assume ownership and manage the lifecycle of the original config, which we will refer to as the "Ephemeral" config going forward.

The Long Term and Ephemeral configs are described as follows.

|Long Term|Ephemeral|
|---|---|
|Managed by you, the user|Managed by os-mfa|
|Contains project information. Does not contain any secrets|Contains project information + temporary authentication token|
|Used as basis to create an Ephemeral config but is otherwise ignored|Used by SDK's and clients for authentication|
|Has a suffix of `-long-term`|Does not have a suffix|
|Manual changes will be passed on to the Ephemeral config|Manual changes will be overwritten|

The "Long Term" and "Ephemeral" configs coexist in the same clouds.yaml file. For example: Here's an annotated example of a `clouds.yaml` file with a Long Term and Ephemeral config.

```yaml
clouds:
    # Managed by os-mfa, Ephemeral.
    catalystcloud:
        auth_type: token # Managed by os-mfa
        auth:
            auth_url: https://api.nz-hlz-1.catalystcloud.io:5000 # Inherited
            project_id: 33735662374f4b7a9621631f2e7e5e15         # Inherited
            project_name: john-smith    # Inherited
            token: gAAAAABjrN[...]e6vqt # Ephemeral, Managed by os-mfa
        region_name: nz-hlz-1           # Inherited
        interface: public               # Inherited
        identity_api_version: 3         # Inherited

    # Managed by you - the user.
    catalystcloud-long-term:
        auth:
            auth_url: https://api.nz-hlz-1.catalystcloud.io:5000
            username: john.smith@example.com
            project_id: 33735662374f4b7a9621631f2e7e5e15
            project_name: john-smith
            user_domain_name: Default
        region_name: nz-hlz-1
        interface: public
        identity_api_version: 3
```

Just the same as openstack sdk's and clients, os-mfa finds your cloud.yaml file by checking the following locations in order:

  * Current directory (`./clouds.yaml`)
  * `~/config/openstack/clouds.yaml`
  * `/etc/openstack/clouds.yaml`

We specify which config we are working with by setting the `OS_CLOUD` environment variable.

```bash
export OS_CLOUD=catalystcloud
```

When we run os-mfa, it will check our `clouds.yaml` file for a long term profile called `<OS_CLOUD>-long-term`. E.g. `catalystcloud-long-term`.

If a long term config does not exist, os-mfa will try to create a default long term config for us based on the original config and sanitized of sensitive values.

Once os-mfa finds (or creates) the Long Term Config os-mfa will then:

 1. Read the project information from the long term config `<OS_CLOUD>-long-term`
 2. Prompt for your secret credentials (password, MFA code)
 3. Swap your credentials (username, password and MFA code) for an authorized token
 4. Create/update a token based Ephemeral configuration in your `clouds.yaml` named `<OS_CLOUD>`

## Run tests

```
python -m unittest discover
```

## Building Package

Source: https://realpython.com/pypi-publish-python-package/

```
python -m pip install pip-tools
pip-compile pyproject.toml
```

## TODO:

 * [/] TBH I am probably going to port this back to python
 * [/] Alert if no clouds.yaml found
 * [/] Better error message if OS_CLOUD not set
 * Non-interactive mode
 * Sanitize long-term config better
 * Store and check expiry of token
    * Only reauthenticate if token is not valid
    * -f, --force cli option to force authentication