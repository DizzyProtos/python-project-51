import argparse
import sys
from requests.exceptions import HTTPError, ConnectionError
from page_loader.loader_logs import logger
from page_loader.loader import download


def _exit_with_error(error_message, page_url, e):
    print(error_message)
    logger.error(f'Exception while downloading {page_url}')
    logger.exception(e)
    sys.exit(1)


def main(*args, **kwargs):
    parser = argparse.ArgumentParser(description='Save page to a folder')
    parser.add_argument('url', type=str, help='page url')
    parser.add_argument('-o', type=str, dest='save_path',
                        help='path to save page', required=True)

    args = parser.parse_args()
    try:
        html_path = download(args.url, args.save_path)
    except ConnectionError as e:
        _exit_with_error(f"Can't get page at {args.url}", args.url, e)
    except HTTPError as e:
        _exit_with_error('Website is not available', args.url, e)
    except IOError as e:
        _exit_with_error("Can't write html file to disk", args.url, e)
    except Exception as e:
        _exit_with_error("Can't download page", args.url, e)
    print(f'Page saved as "{html_path}"')


if __name__ == '__main__':
    main()
