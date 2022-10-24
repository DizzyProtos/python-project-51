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
site_urls = [
    'mock://test_test.com',
    'mock://test_test.com/my/wer/wer/wer'
]


def itterate_resources(html_text):
    website = soup(html_text)
    for resource in website.find_all(resource_tags):
        if not resource.has_attr('src'):
            continue
        if urlparse(resource['src']).netloc:
            continue
        yield resource['src']
        

def check_if_resources_exist(html_text, save_folder):
    for src in itterate_resources(html_text):
        resource_path = os.path.join(save_folder, src)
        if not os.path.isfile(resource_path):
            return False
    return True


def get_mocked_resources(html_text, site_url):
    parsed_uri = urlparse(site_url)
    site_url = f'{parsed_uri.scheme}://{parsed_uri.netloc}'

    mock_dict = {}
    for src in itterate_resources(html_text):
        mock_url = f'{site_url}/{src}'
        resource_path = os.path.join('tests', 'fixtures', src)
        resource_path = resource_path.replace('/', os.path.sep)
        with open(resource_path, 'rb') as rf:
            mock_dict[mock_url] = rf
    return mock_dict


@pytest.mark.parametrize('site_url', site_urls)
def test_page_loader(site_url):
    htmp_page_path = 'tests/fixtures/page.html'
    with open(htmp_page_path, 'r') as f:
        page_text = f.read()
    
    save_folder = './tmp/'
    if not os.path.isdir(save_folder):
        os.mkdir(save_folder)
    resources_urls = get_mocked_resources(page_text, site_url)
    with requests_mock.Mocker(real_http=True) as m:
        m.get(site_url, text=page_text)
        for mock_url, content in resources_urls.items():
            m.get(mock_url, body=content)

        output_file = download(site_url, save_folder)

    with open(output_file, 'r') as f:
        downloaded_text= f.read()
    assert check_if_resources_exist(downloaded_text, save_folder)

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
