# os-mfa

Convenient and secure OpenStack authentication and credential management inspired by [broamski/aws-mfa](https://github.com/broamski/aws-mfa)

## What problem does os-mfa solve?

First some quick background. OpenStack provides two main methods of setting credentials for programmatic authentication:

**A) [Environment variables set via 'openrc.sh' files](https://docs.openstack.org/newton/user-guide/common/cli-set-environment-variables-using-openstack-rc.html)**

* 🛡️ Avoids storing passwords in plaintext on disk 👍
* 🤦 Session credentials are lost if you close or restart your terminal window 👎
* 🔒 Sessions can't be shared/accessed across multiple terminal sessions 👎
* 💔 Not compatible with windows clients 👎

**B) [clouds.yaml configuration files](https://docs.openstack.org/python-openstackclient/latest/configuration/index.html#configuration-files)**

 * 💪 Session tokens are durable to terminal restarts/shutdowns 👍
 * 💗 Compatible and consistent user experience across platforms 👍
 * 🌏 OpenStack sessions are accessible in from any terminal session 👍
 * 🙈 Encourages credentials to be stored in plain text 👎
 * ⌛ Tokens that expire after 12 hours need to be manually refreshed and updated in clouds.yaml 👎

As we can see both have advantages and disadvantages. But what if we could have the best parts of both options?

**🌈 os-mfa 🦄 leverages the convenience and durability of using `clouds.yaml` and automates the secure management of credentials and tokens**

 * 🛡️ Avoids storing passwords in plaintext on disk 👍
 * 💪 Session tokens are durable to terminal restarts/shutdowns 👍
 * 💗 Compatible and consistent user experience across platforms 👍
 * 🌏 OpenStack sessions are accessible in from any terminal session 👍
 * 🔀 Trivially switch between multiple authenticated OpenStack sessions 👍
 * 🤝 Ensured compatibility with the OpenStack ecosystem 👍

## Quick start

Install os-mfa

```bash
pip install -U os-mfa
```

Download `clouds.yaml` file from your OpenStack dashboard. For example

 1. Click **[API Access](https://dashboard.catalystcloud.nz/project/api_access/)** from the top left of the dashboard
 2. Click **Download OpenStack RC File** on the top right
 3. Select **OpenStack clouds.yaml File** from the drop down

Place the file in your current working directory (`.`) or an alternate [location described by the docs](https://docs.openstack.org/python-openstackclient/latest/configuration/index.html#clouds-yaml)

Linux
  * `~/.config/openstack/clouds.yaml`
  * `/etc/openstack/clouds.yaml`

Windows
  * `C:\Users\<username>\.config\openstack\clouds.yaml`
  * `C:\ProgramData\openstack\clouds.yaml`

E.g.

```yaml
# /home/john/clouds.yaml
clouds:
  catalystcloud:
    auth:
      auth_url: https://api.nz-hlz-1.catalystcloud.io:5000
      project_id: 33735662374f4b7a9621631f2e7e5e15
      project_name: acme-incorporated
      user_domain_name: Default
      username: john.smith@acme.com
      password: 1ns3curE123!
    identity_api_version: 3
    interface: public
    region_name: nz-hlz-1
```

Set `$OS_CLOUD` in your environment.

```bash
$ export OS_CLOUD=catalystcloud
```

Run `os-mfa`

```bash
$ os-mfa
Authenticating 'john.smith@example.com' in project 'john-smith'
Enter Password:
MFA Code (Press enter to skip): 654321
Getting token...
```

```
$ openstack network list
+--------------------------------------+------------+--------------------------------------------+
| ID                                   | Name       | Subnets                                    |
+--------------------------------------+------------+--------------------------------------------+
| f10ad6de-a26d-4c29-8c64-2a7418d47f8f | public-net | 5063aab1-aa08-48b2-b81d-730ac732fc51,      |
|                                      |            | 8a7fe804-7fbe-43d0-aa1d-cfa03034ef22,      |
|                                      |            | a1549e09-4176-4322-860c-cadc68608b48       |
+--------------------------------------+------------+--------------------------------------------+
```

Now if you close/restart or start a new terminal window, resume your existing OpenStack session simply by exporting `$OS_CLOUD` again.

```bash
export OS_CLOUD=catalystcloud
```

## What happened when we ran os-mfa?

The first time we run os-mfa is creates a *"long-term"* configuration in our clouds.yaml without any passwords or secrets.

Long term configurations contain the minimum information required for os-mfa to use to initialize a token based authentication.

 * They should *not* contain any secrets such as tokens or passwords.
 * They are distinguished by a suffix of `-long-term`

os-mfa will then use the `-long-term` configuration to create a token based configuration as follows.

 1. Prompts the user for their password and MFA code
 2. Swaps the password and MFA code for an OpenStack auth token
 3. Updates the original configuration to use the new token for authentication

The resulting clouds.yaml should look like this

```yaml
# /home/john/clouds.yaml
clouds:
  catalystcloud:
    auth:
      auth_url: https://api.nz-hlz-1.catalystcloud.io:5000
      project_id: 33735662374f4b7a9621631f2e7e5e15
      project_name: acme-incorporated
      token: gAAAAABkTkGx4Dah37lkiGTSEe3-r[...]9dQCVTBRsKjg6NFIYgMYRdAk7TTvIPOaaOE
    identity_api_version: 3
    interface: public
    region_name: nz-hlz-1
  catalystcloud-long-term:
    auth:
      auth_url: https://api.nz-hlz-1.catalystcloud.io:5000
      project_id: 33735662374f4b7a9621631f2e7e5e15
      project_name: acme-incorporated
      user_domain_name: Default
      username: john.smith@acme.com
    identity_api_version: 3
    interface: public
    region_name: nz-hlz-1

```

## Going further

### Multiple projects, users and sessions


Since clouds.yaml supports multiple configurations, you can create configurations for any combination of

 * user
 * project
 * region
 * openstack cloud

```yaml
clouds:
  project1:
    region: nz-hlz-1
    auth:
        project_name: project1
        username: john.smith@acme.com
        # ...
  project2:
    region: nz-por-1
    auth:
        project_name: project2
        username: john.smith@acme.com
        # ...
```

After initializing a token based authentication for each configuration using os-mfa, you can change between sessions at will

```bash
OS_CLOUD=project1
```
```bash
OS_CLOUD=project2
```

## Contributing

Nothing special to report, just raise a PR

### Run tests

```
python -m unittest discover
```

### Building Package

Source: https://realpython.com/pypi-publish-python-package/

```
python -m pip install pip-tools twine
pip-compile pyproject.toml
rm -rf dist/*
python -m build
twine check dist/*
twine upload -r testpypi dist/*
twine upload dist/*
```

## TODO

 * ☑️ TBH I am probably going to port this back to python
 * ☑️ Alert if no clouds.yaml found
 * ☑️ Better error message if OS_CLOUD not set
 * 🟦 CI/CD
 * 🟦 Optionally disable prompt for MFA token
 * 🟦 Store and check expiry of token
 * 🟦 Only reauthenticate if token is not valid
 * 🟦 -f, --force cli option to force authentication
 * 🟦 more unit and integration tests
