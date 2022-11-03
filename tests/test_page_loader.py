import json
import os
from bs4 import BeautifulSoup as soup

import pytest
import filecmp
from requests.exceptions import ConnectionError
import shutil
import requests_mock
from page_loader.loader import download


resource_tags = ['img', 'link', 'script', 'a']
site_url = 'https://site.com/'


def itterate_resources(html_text):
    website = soup(html_text)
    for resource in website.find_all(resource_tags):
        attr = ''
        if resource.has_attr('src'):
            attr = 'src'
        elif resource.has_attr('href'):
            attr = 'href'
        else:
            continue
        if 'site-com_files' not in resource[attr]:
            continue
        yield resource[attr]


def check_if_resources_exist(html_text, save_folder):
    count = 0
    for src in itterate_resources(html_text):
        src = src.replace('/', os.path.sep)
        resource_path = os.path.join(save_folder, src)
        if not os.path.isfile(resource_path):
            return False
        count += 1
    return count


def test_page_loader():
    htmp_page_path = 'tests/fixtures/page.html'
    with open(htmp_page_path, 'r') as f:
        page_text = f.read()

    save_folder = f'.{os.path.sep}tmp'
    if not os.path.isdir(save_folder):
        os.mkdir(save_folder)

    with open('tests/fixtures/resources_urls.json', 'r') as f:
        resources_urls = json.load(f)

    local_file_uri = f"file:///{os.getcwd().replace(os.path.sep, '/')}"
    with requests_mock.Mocker(real_http=True) as m:
        m.get(site_url, text=page_text)
        for mock_url, file_path in resources_urls.items():            
            file_uri = f'{local_file_uri}/{file_path}'
            m.get(mock_url, body=file_uri)

        output_file = download(site_url, save_folder)

    with open(output_file, 'r') as f:
        downloaded_text = f.read()

    assert check_if_resources_exist(downloaded_text, save_folder) == 4
    assert filecmp.cmp(output_file, './tests/fixtures/correct_page.html')

    os.remove(output_file)
    shutil.rmtree(save_folder)


def test_connection_error():
    with pytest.raises(ConnectionError):
        if not os.path.isdir('./connection_error/'):
            os.mkdir('./connection_error/')
        download('http://badqwref23site.com', './connection_error/')
    shutil.rmtree('./connection_error/')


def test_non_existing_path():
    with pytest.raises(IOError):
        download('http://google.com', './ioerror/ioerror/ioerror/')
