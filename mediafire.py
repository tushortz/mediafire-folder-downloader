import json
import os
import requests
import sys
import re
import click


def download_file(file_dict, folder_name="tmp"):
    """Download file using the file data"""
    
    filename = file_dict.get("filename")
    url = file_dict["links"]["normal_download"]
    quick_key = file_dict["quickkey"]

    print("Generating link ...")

    page = requests.get(url).text
    regex = f'href="(http.*?/{quick_key}/.*?)"'
    link = re.search(regex, page).group(1)
    size = int(file_dict.get("size", "0"))

    r = requests.get(link)
    chunks = r.iter_content(chunk_size=1024)
    filepath = f"{folder_name}/{filename}"

    with click.progressbar(
        chunks,
        length=size,
        label=f"Downloading {filename}",
        show_percent=True,
        show_pos=True,
        show_eta=True,
        width=50,
        color="g"
    ) as bar, open(filepath, "wb") as f:
        for chunk in bar:
            f.write(chunk)
            f.flush()
            bar.update(len(chunk))


def main():
    api_url = "https://www.mediafire.com/api/1.4/folder/get_content.php"
    folder_api_url = "https://www.mediafire.com/api/1.4/folder/get_info.php?r=osqf"

    session = requests.Session()
    session.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    })

    url = sys.argv[1]

    folder_key = re.search(r"folder/(.*?)/", url).group(1)

    params = {
        "r": "budo",
        "content_type": "files",
        "filter": "all",
        "order_by": "name",
        "order_direction": "asc",
        "chunk": 1,
        "version": 1.5,
        "folder_key": f"{folder_key}",
        "response_format": "json"
    }

    response = session.get(api_url, params=params).json()
    response = response.get("response", {})
    response = response.get("folder_content", {})

    post_data = {
        "folder_key": folder_key,
        "recursive": "yes",
        "response_format": "json"
    }

    folder_info = session.post(folder_api_url, post_data).json()
    folder_name = folder_info["response"]["folder_info"]["name"]

    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    for content in response.get("files", []):
        download_file(content, folder_name)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(f"Usage: python {__file__} <<mediafire_folder_url>>")

    main()
