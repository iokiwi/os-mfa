#!/usr/bin/env bash
export OS_CLOUD=catalystcloud
rm -rf clouds.yaml
cp clouds.yml clouds.yaml
./venv/bin/python openstack-profile-manager/main.py
