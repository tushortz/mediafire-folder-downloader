#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys

import requests
from tqdm import tqdm

CHUNK_SIZE = 512 * 1024  # 512 KB


def download_file(file_dict, folder_name="tmp"):
    """Downloads the file using the file metadata"""

    filename = file_dict.get("filename")
    url = file_dict["links"]["normal_download"]

    page = requests.get(url).text
    link = re.search(r'href="((http|https)://download[^"]+)', page)

    if link:
        link = link.group(1)
    else:
        print("Can't parse download link for {filename}")
        return

    size = int(file_dict.get("size", "0"))

    res = requests.get(link, stream=True)
    filepath = f"{folder_name}/{filename}"

    with open(filepath, "wb") as f:
        pbar = tqdm(total=size, unit="B", unit_scale=True, desc=filename)
        for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
            f.write(chunk)
            pbar.update(len(chunk))


def download_folder(folder_url: str):
    """Downloads the contents of the folder."""
    api_url = "https://www.mediafire.com/api/1.5/folder/get_content.php"
    folder_api_url = "https://www.mediafire.com/api/1.5/folder/get_info.php?r=osqf"

    session = requests.Session()
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }

    folder_key = re.search(r"folder/(\w+)/?", folder_url).group(1)

    params = {
        "r": "budo",
        "content_type": "files",
        "filter": "all",
        "order_by": "name",
        "order_direction": "asc",
        "chunk": 1,
        "version": 1.5,
        "folder_key": f"{folder_key}",
        "response_format": "json",
    }

    response = session.get(api_url, params=params).json()
    response = response.get("response", {})
    response = response.get("folder_content", {})

    post_data = {
        "folder_key": folder_key,
        "recursive": "yes",
        "response_format": "json",
    }

    folder_info = session.post(folder_api_url, post_data).json()
    folder_info = folder_info["response"]

    if folder_info.get("folder_info") is None:
        sys.stderr.write("Error: Invalid folder url")
        return

    folder_name = folder_info["folder_info"]["name"]

    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    for content in response.get("files", []):
        download_file(content, folder_name)


def main():
    desc = "Simple command-line script to download files from a mediafire folder."

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "folder_url", nargs=1, help="Mediafire folder url to download from"
    )
    args = parser.parse_args()
    download_folder(args.folder_url[0])


if __name__ == "__main__":
    main()
