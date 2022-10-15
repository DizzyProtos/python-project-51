import sys
import os
import argparse
from page_loader.loader import download


sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


def main(*args, **kwargs):
    parser = argparse.ArgumentParser(description='Save page to a folder')
    parser.add_argument('url', type=str, help='page url')
    parser.add_argument('save_path', type=str, help='path to save page')

    args = parser.parse_args()
    download(page_url=args.url, save_folder=args.save_path)


if __name__ == '__main__':
    main()
