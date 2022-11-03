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


@pytest.fixture
def output_folder():
    save_folder = f'.{os.path.sep}tmp'
    if not os.path.isdir(save_folder):
        os.mkdir(save_folder)
    yield save_folder
    shutil.rmtree(save_folder)


@pytest.fixture
def html_page():
    html_page_path = 'tests/fixtures/page.html'
    with open(html_page_path, 'r') as f:
        page_text = f.read()
    return page_text


@pytest.fixture
def resources():
    with open('tests/fixtures/resources_urls.json', 'r') as f:
        resources_urls = json.load(f)
    return resources_urls


@pytest.fixture
def mocker(html_page, resources):
    local_file_uri = f"file:///{os.getcwd().replace(os.path.sep, '/')}"
    with requests_mock.Mocker(real_http=False) as mock:
        mock.get(site_url, text=html_page)
        for mock_url, file_path in resources.items():            
            file_uri = f'{local_file_uri}/{file_path}'
            mock.get(mock_url, body=file_uri)
        yield mock


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


def test_page_loader(mocker, output_folder):
    output_file = download(site_url, output_folder)

    with open(output_file, 'r') as f:
        downloaded_text = f.read()

    assert check_if_resources_exist(downloaded_text, output_folder) == 4
    assert filecmp.cmp(output_file, './tests/fixtures/correct_page.html')

    os.remove(output_file)


def test_connection_error(output_folder):
    with pytest.raises(ConnectionError):
        download('http://badqwref23site.com', output_folder)


def test_non_existing_path(output_folder):
    with pytest.raises(IOError):
        download('http://google.com', output_folder)
