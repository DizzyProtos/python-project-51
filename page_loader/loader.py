import os
from urllib.parse import urlparse
from progress.bar import Bar
import requests as re
from bs4 import BeautifulSoup as soup
from page_loader.loader_logs import logger
from page_loader.resource_loader import download_resource


ATTRS_MAP = {
    'link': 'href',
    'img': 'src',
    'script': 'src'
}


def _get_output_filename(page_url):
    parsed_uri = urlparse(page_url)
    netloc_str = parsed_uri.netloc.replace('.', '-')
    path_str = parsed_uri.path.replace('/', '-')
    file_name = f"{netloc_str}{path_str}.html"
    file_name = file_name.replace('/', os.path.sep)
    return file_name


def _iterate_resource_tags(resources, page_url):
    for tag in resources:
        attr = ATTRS_MAP[tag.name]
        if not tag.has_attr(attr):
            continue
        parsed_url = urlparse(page_url)
        netloc = urlparse(tag[attr]).netloc
        if (netloc == '') or parsed_url.netloc == netloc:
            yield tag


def _fetch_resource(tag, page_url, save_folder):
    attr = ATTRS_MAP[tag.name]
    logger.info(f'Getting {tag.name} from {tag[attr]}')
    resource_path = download_resource(page_url, tag[attr], save_folder)
    if not resource_path:
        logger.error(f"Can't download {tag[attr]}")
        return None
    logger.info(f'Saved {tag.name} to {resource_path}')
    return resource_path


def download(page_url, save_folder):
    if page_url[-1] == '/':
        page_url = page_url[:-1]

    if not os.path.isdir(save_folder):
        raise IOError(f'path {save_folder} does not exist')

    logger.info(f'Dowloading {page_url}')
    bar = Bar('Downloading', max=100)
    response = re.get(page_url)
    response.raise_for_status()

    logger.info(f'Got {page_url} successfully')
    bar.next(20)

    output_filename = _get_output_filename(page_url)
    resources_folder = f"{output_filename.replace('.html', '_files')}"
    resources_folder = os.path.join(save_folder, resources_folder)
    if not os.path.isdir(resources_folder):
        os.mkdir(resources_folder)

    parsed_html = soup(response.text, 'html.parser')
    resources = parsed_html.find_all(ATTRS_MAP.keys())
    for tag in _iterate_resource_tags(resources, page_url):
        resource_path = _fetch_resource(tag, page_url, resources_folder)
        if not resource_path:
            continue
        tag[ATTRS_MAP[tag.name]] = resource_path
        bar.next(80 // len(resources))

    save_file_path = os.path.join(save_folder, output_filename)
    logger.info(f'Saving page to {save_file_path}')
    with open(save_file_path, 'w') as html:
        html.write(parsed_html.prettify())
    bar.finish()
    return save_file_path
