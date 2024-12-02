#!/usr/bin/env python3
# coding:utf-8
# Version: 1.0.12

def get_linux_distribution():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distribution_id = line.strip().split("=")[1].strip('"')
                elif line.startswith("NAME="):
                    distribution_name = line.strip().split("=")[1].strip('"')
        return distribution_id, distribution_name
    except FileNotFoundError:
        return None, None

distribution_id, distribution_name = get_linux_distribution()

if distribution_id is not None and distribution_id == "debian":
    from .rk3390 import *
else:
    from .jetson import *
