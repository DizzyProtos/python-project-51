import os
import shutil
from urllib.parse import urlparse
from progress.bar import Bar
from bs4 import BeautifulSoup as soup
import requests as re
from page_loader.loader_logs import logger


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


def _download_resource(page_url, resource_path, save_folder):
    parsed_uri = urlparse(page_url)
    page_url = f'{parsed_uri.scheme}://{parsed_uri.netloc}'
    if resource_path[0] == '/':
        resource_path = resource_path[1:]

    resource_uri = f'{page_url}/{resource_path}'
    if urlparse(resource_path).netloc:
        resource_uri = resource_path
    resource = re.get(resource_uri, stream=True)
    if resource.status_code // 100 != 2:
        return None

    parsed_uri = urlparse(resource_uri)
    host_part = parsed_uri.netloc.replace('.', '-')
    path_part = parsed_uri.path.replace('/', '-')
    resource_name = f"{host_part}{path_part}"
    local_path = os.path.join(save_folder, resource_name)
    try:
        os.makedirs(os.path.split(local_path)[0])
    except FileExistsError:
        pass

    with open(local_path, 'wb') as output:
        shutil.copyfileobj(resource.raw, output)
    asset_path = '/'.join(local_path.split(os.path.sep)[-2:])
    return asset_path


def download(page_url, save_folder):
    if page_url[-1] == '/':
        page_url = page_url[:-1]

    if not os.path.isdir(save_folder):
        raise IOError(f'path {save_folder} does not exist')

    logger.info(f'Dowloading {page_url}')
    bar = Bar('Downloading', max=100)
    response = re.get(page_url)
    if response.status_code != 200:
        raise re.exceptions.HTTPError()
    logger.info(f'Got {page_url} successfully')
    bar.next(20)

    output_filename = _get_output_filename(page_url)
    resources_folder = f"{output_filename.replace('.html', '_files')}"
    resources_folder = os.path.join(save_folder, resources_folder)
    if not os.path.isdir(resources_folder):
        os.mkdir(resources_folder)

    parsed_url = urlparse(page_url)
    website = soup(response.text, 'html.parser')

    resources = website.find_all(ATTRS_MAP.keys())
    for tag in resources:
        attr = ATTRS_MAP[tag.name]

        netloc = urlparse(tag[attr]).netloc
        if (netloc == '') or parsed_url.netloc == netloc:
            logger.info(f'Getting {tag.name} from {tag[attr]}')
            resource_path = _download_resource(page_url, tag[attr], resources_folder)
            if not resource_path:
                logger.error(f"Can't download {tag[attr]}")
                continue
            logger.info(f'Saved {tag.name} to {resource_path}')
            tag[attr] = resource_path
        bar.next(80 // len(resources))

    save_file_path = os.path.join(save_folder, output_filename)
    logger.info(f'Saving page to {save_file_path}')
    with open(save_file_path, 'w', encoding='utf-8') as html:
        html.write(website.prettify())
    return save_file_path
