import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from bs4 import BeautifulSoup as soup

import pytest
from requests.exceptions import ConnectionError
import shutil
from urllib.parse import urlparse
import requests_mock
from page_loader.loader import download



resource_tags = ['img', 'link', 'script', 'a']
site_url = 'https://site.com/'


def itterate_resources(html_text):
    parsed_site = urlparse(site_url)
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
    resources_urls = {
        'https://site.com/assets/scripts.js': 'file:///C:/Users/medve/Desktop/python-project-51/tests/fixtures/scripts.js',
        'https://site.com/photos/me.jpg': 'file:///C:/Users/medve/Desktop/python-project-51/tests/fixtures/photos/me.jpg',
        'https://site.com/blog/about/assets/styles.css': 'file:///C:/Users/medve/Desktop/python-project-51/tests/fixtures/assets/styles.css',
        'https://cdn2.site.com/blog/assets/style.css': 'file:///C:/Users/medve/Desktop/python-project-51/tests/fixtures/assets/styles.css'
    }
    with requests_mock.Mocker(real_http=True) as m:
        m.get(site_url, text=page_text)
        for mock_url, content in resources_urls.items():
            m.get(mock_url, body=content)

        output_file = download(site_url, save_folder)

    with open(output_file, 'r', encoding='utf-8') as f:
        downloaded_text= f.read()
    
    assert check_if_resources_exist(downloaded_text, save_folder) == 4

    os.remove(output_file)
    shutil.rmtree(save_folder)


def test_connection_error():
    with pytest.raises(ConnectionError):
        if not os.path.isdir('./connection_error/'):
            os.mkdir('./connection_error/')
        download('http://badqwref23site.com', './connection_error/')
    shutil.rmtree('./connection_error/')


def test_non_existing_path():
    with pytest.raises(IOError) as e:
        download('http://google.com', './ioerror/ioerror/ioerror/')
