# os-mfa

Convenient and secure OpenStack authentication and credential management inspired by [broamski/aws-mfa](broamski/aws-mfa)

## What problem does os-mfa solve?

First some quick background. OpenStack provides two main methods of setting credentials for programmatic authentication:

**A) [Environment variables set via 'openrc.sh' files](https://docs.openstack.org/newton/user-guide/common/cli-set-environment-variables-using-openstack-rc.html)**

* 🛡️ Avoids storing passwords in plaintext on disk 👍<br>
* 🤦 Session credentials are lost if you close or restart your terminal window 👎<br>
* 🔒 Sessions can't be shared/accessed across multiple terminal sessions 👎<br>
* 💔 Not compatible with windows clients 👎<br>

**B) [clouds.yaml configuration files](https://docs.openstack.org/python-openstackclient/latest/configuration/index.html#configuration-files)**

 * 🌏 Are accessible in every terminal session 👍
 * 💪 Are durable to restarts/shutdowns 👍
 * 💗 Compatible and consistent user experience across platforms 👍
 * 🙈 Encourages credentials to be stored in plain text 👎
 * ⌛ Tokens expire after 12 hours and need to be manually refreshed and updated in clouds.yaml 👎

As we can see both have advantages and disadvantages. But what if we could have the best parts of both options?

**🌈 os-mfa 🦄 leverages the convenience and durability of using `clouds.yaml` and automates the secure management of credentials and tokens**

 * 🛡️ Avoids storing passwords in plaintext on disk 👍
 * 🌏 Session credentials are accessible in all terminals sessions 👍
 * 💪 Are durable to restarts/shutdowns 👍
 * 🔀 Trivially switch between multiple authenticated OpenStack sessions 👍
 * 🤝 Ensures native compatibility with the OpenStack ecosystem 👍
 * 💗 Compatible and consistent user experience across platforms 👍

## Quick start

Install os-mfa

```bash
pip install -U os-mfa
```

Download `clouds.yaml` file from your OpenStack dashboard. For example

 1. Click API Access https://dashboard.catalystcloud.nz/project/api_access/
 2. Click **Download OpenStack RC File** on the top right
 3. Select **OpenStack clouds.yaml File** from the drop down



Place the file in your current working directory (`.`) or an alternate [location described by the docs](https://docs.openstack.org/python-openstackclient/latest/configuration/index.html#clouds-yaml)

Linux
  * `~/.config/openstack/clouds.yaml`
  * `/etc/openstack/clouds.yaml`

Windows
  * `C:\Users\you\.config\openstack\clouds.yaml`
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

Run os-mfa

```bash
$ export OS_CLOUD=catalystcloud
```
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

If you close/restart or start a new terminal window, resume your openstack session simply by exporting `$OS_CLOUD` again.

```bash
export OS_CLOUD=catalystcloud
```

## What happened when we ran os-mfa?

os-mfa created a *"long-term"* configuration without any passwords or secrets.

 * *"long-term"* configurations are distinguished with a suffix of `-long-term`
 * We do not use the long term configs with the openstack client tools.
 
The long term config used as a foundation for authentication by os-mfa which then:

1) Prompts the user for their password and totp token

2) Swaps the password and totp for an openstack auth token

3) Updates the original configuration to use the new token for authentication

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


### Switching between multiple cloud accounts and sessions

```yaml
clouds:
  project1-long-term:
    region: nz-hlz-1
    auth:
        project_name: project1
        username: john.smith@acme.com
        # ...
  project2-long-term:
    region: nz-por-1
    auth:
        project_name: project2
        username: john.smith@acme.com
        # ...
```

After running os-mfa once for each project you can switch between them 

```
OS_CLOUD=project1
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
python -m pip install pip-tools build twine bumpver
pip-compile pyproject.toml
python -m build
twine check dist/*
twine upload -r testpypi dist/*
twine upload dist/*
```

## TODO

 * ☑️ TBH I am probably going to port this back to python
 * ☑️ Alert if no clouds.yaml found
 * ☑️ Better error message if OS_CLOUD not set
 * ☑️ CI/CD
 * 🟦 Non-interactive mode
 * 🟦 Sanitize long-term config better
 * 🟦 Store and check expiry of token
    * 🟦 Only reauthenticate if token is not valid
    * 🟦 -f, --force cli option to force authentication