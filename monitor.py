import requests
import json
import logging
import time

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)-10s - %(message)s'))
    logger.addHandler(sh)
    return logger

def main():
    logger = setup_logger()

    errors = []
    filename = 'sites.json'
    with open(filename) as fh:
        config = json.load(fh)
    for site in config["sites"]:
        url = site["url"]
        logger.info(f"URL: {url}")
        if 'enabled' in site and not site['enabled']:
            continue

        start = time.time()
        resp = requests.get(url, allow_redirects=False)
        end = time.time()
        logger.info(f"status_code: {resp.status_code}")
        logger.info(f"headers: {resp.headers}")
        logger.info(f"elaspsed time: {end - start}")
        if resp.status_code != site["status_code"]:
            errors.append(f'URL {url} expected {site["status_code"]} received {resp.status_code}')

        if 'headers' in site:
            for header in site["headers"]:
                if header in resp.headers:
                    if site["headers"][header] != resp.headers[header]:
                        errors.append(f'URL {url} is expected to have header {header}={site["headers"][header]} but it is {resp.headers[header]}')
                else:
                    errors.append(f'URL {url} is expected to have a header "{header}" but it is missing')

        if 'html_contains' in site:
            if site['html_contains'] not in resp.content.decode('utf-8'):
                errors.append(f'URL {url} expected some html_content but did not receive it')

    if errors:
        for error in errors:
            logger.error(error)
        exit(1)
    else:
        logger.info("Everything is fine")
        exit(0)
if __name__ == '__main__':
    main()