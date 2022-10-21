import os
import uuid
import validators
import shutil
from progress.bar import Bar
from bs4 import BeautifulSoup as soup
import requests as re
from page_loader.loader_logs import logger


def _download_resource(resource_url, save_folder):
    resource = re.get(resource_url, stream=True)
    if resource.status_code // 100 != 2:
        return None

    local_path = resource_url.split('//')[1].replace('/', os.path.sep)
    resource_path = os.path.join(save_folder, local_path)
    try:
        os.makedirs(os.sep.join(resource_path.split(os.path.sep)[:-1]))
    except FileExistsError:
        pass

    if resource_path[-1] == os.path.sep:
        filename = uuid.uuid4().hex
        resource_path += filename
        local_path += filename

    with open(resource_path, 'wb') as output:
        shutil.copyfileobj(resource.raw, output)

    return local_path


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

    website = soup(response.text, 'html.parser')
    resource_tags = ['img', 'link', 'script', 'a']
    resources = website.find_all(resource_tags)
    for tag in resources:
        if tag.has_attr('src'):
            logger.info(f'Getting {tag.name} from {tag["src"]}')
            resource_url = tag['src']
            if not validators.url(resource_url):
                if resource_url[0] == '/':
                    resource_url = resource_url[1:]
                resource_url = f'{page_url}/{resource_url}'
            local_path = _download_resource(resource_url, save_folder)
            if not local_path:
                logger.error(f"Can't download {resource_url}")
                continue
            tag['src'] = local_path
        bar.next(80 // len(resources))

    file_name = page_url.split('//')[1]
    file_name = ''.join(file_name.split('.')[:-1])
    file_name = ''.join([ch if ch.isalpha() else '-' for ch in file_name])
    file_name += '.html'
    save_file_path = os.path.join(save_folder, file_name)
    logger.info(f'Saving page to {save_file_path}')
    with open(save_file_path, 'w', encoding='utf-8') as html:
        html.write(website.prettify())
    return save_file_path
