#!/usr/bin/env python3
# coding:utf-8
# Version: 1.0.6

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

if distribution_id is not None:
    if distribution_id == "ubuntu":
        # print("The system is running Ubuntu.")
        from .jetson import *
    elif distribution_id == "debian":
        # print("The system is running Debian.")
        from .rk3390 import *
    else:
        print(f"The system is running {distribution_name} ({distribution_id}).")
else:
    print("This is not a Linux system or /etc/os-release is not found.")
