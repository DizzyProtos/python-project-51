import os
import shutil
from urllib.parse import urlparse
import requests as re
from requests.compat import urljoin


def _get_resource_local_path(resource_uri, save_folder):
    parsed_uri = urlparse(resource_uri)
    host_part = parsed_uri.netloc.replace('.', '-')
    path_part = parsed_uri.path.replace('/', '-')
    resource_name = f"{host_part}{path_part}"
    if '.' not in resource_name:
        resource_name += '.html'
    return os.path.join(save_folder, resource_name)


def _fetch_resource(page_url, resource_path):
    if urlparse(resource_path).netloc:
        resource_uri = resource_path
    else:
        resource_uri = urljoin(page_url, resource_path)
    resource = re.get(resource_uri, stream=True)
    if resource.status_code // 100 != 2:
        return None
    return resource, resource_uri


def download_resource(page_url, resource_path, save_folder):
    resource, resource_uri = _fetch_resource(page_url, resource_path)
    if not resource_uri:
        return None

    local_path = _get_resource_local_path(resource_uri, save_folder)
    try:
        os.makedirs(os.path.split(local_path)[0])
    except FileExistsError:
        pass

    with open(local_path, 'wb') as output:
        shutil.copyfileobj(resource.raw, output)
    asset_path = '/'.join(local_path.split(os.path.sep)[-2:])
    return asset_path
