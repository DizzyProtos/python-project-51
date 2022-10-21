import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from bs4 import BeautifulSoup as soup

import pytest
from requests.exceptions import ConnectionError
import shutil
import requests_mock
from page_loader.loader import download


def check_if_resource_exists(html_text, save_folder):
    website = soup(html_text)
    resource_tags = ['img', 'link', 'script', 'a']
    for resource in website.find_all(resource_tags):
        if not resource.has_attr('src'):
            continue
        resource_path = os.path.join(save_folder, resource['src'])
        if not os.path.isfile(resource_path):
            return False
    return True


def test_page_loader():
    with open('tests/fixtures/page.html', 'r') as f:
        page_text = f.read()
    
    site_url = 'mock://test_test.com'
    save_folder = './tmp/'
    if not os.path.isdir(save_folder):
        os.mkdir(save_folder)
    with requests_mock.Mocker(real_http=True) as m:
        m.get(site_url, text=page_text)
        output_file = download(site_url, save_folder)

    with open(output_file, 'r') as f:
        downloaded_text= f.read()
    assert check_if_resource_exists(downloaded_text, save_folder)
    downloaded_website = soup(downloaded_text, 'html.parser')
    for tag in downloaded_website.find_all():
        tag.attrs.pop('src', None)
    with open('tests/fixtures/correct_page.html', 'r') as f:
        correct_output = f.read()
    correct_website = soup(correct_output)
    for tag in correct_website.find_all():
        tag.attrs.pop('src', None)
    assert str(downloaded_website) == str(correct_website)
    os.remove(output_file)
    shutil.rmtree(save_folder)


def test_connection_error():
    with pytest.raises(ConnectionError) as e:
        download('http://badqwref23site.com', './connection_error/')


def test_non_existing_path():
    with pytest.raises(IOError) as e:
        download('http://google.com', './ioerror/ioerror/ioerror/')
