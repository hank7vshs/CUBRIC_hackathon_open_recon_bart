#!/usr/bin/python3
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

import json
import argparse

def extract_info(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            general = data.get("general", {})
            vendor = general.get("vendor", "N/A")
            id_ = general.get("id", "N/A")
            version = general.get("version", "N/A")

            print(vendor, id_, version)

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")

    except json.JSONDecodeError:
        print(f"Error: File '{file_path}' is not a valid JSON file.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract vendor, id, and version from the config file.")
    parser.add_argument("file", help="Path to the JSON file")
    args = parser.parse_args()

    extract_info(args.file)
