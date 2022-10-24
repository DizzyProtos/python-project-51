import os
import shutil
from urllib.parse import urlparse
from progress.bar import Bar
from bs4 import BeautifulSoup as soup
import requests as re
from page_loader.loader_logs import logger


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

    resource = re.get(f'{page_url}/{resource_path}', stream=True)
    if resource.status_code // 100 != 2:
        return None

    parsed_uri = urlparse(page_url)
    netloc_str = parsed_uri.netloc.replace('.', '-')
    resource_name = f"{netloc_str}-{resource_path.replace('/', '-')}"
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

    website = soup(response.text, 'html.parser')
    resource_tags = ['img', 'link', 'script', 'a']
    resources = website.find_all(resource_tags)
    for tag in resources:
        if tag.has_attr('src'):
            src = tag['src']
            if urlparse(src).netloc:
                continue
            logger.info(f'Getting {tag.name} from {tag["src"]}')
            resource_path = _download_resource(page_url, src, resources_folder)
            if not resource_path:
                logger.error(f"Can't download {src}")
                continue
            logger.info(f'Saved {tag.name} to {resource_path}')
            tag['src'] = resource_path
        bar.next(80 // len(resources))

    save_file_path = os.path.join(save_folder, output_filename)
    logger.info(f'Saving page to {save_file_path}')
    with open(save_file_path, 'w', encoding='utf-8') as html:
        html.write(website.prettify())
    return save_file_path
