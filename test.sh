#!/usr/bin/env bash
rm -rf clouds.yml
cp clouds_.yml clouds.yml
./venv/bin/python -m os_mfa --os-cloud=catalystcloud
