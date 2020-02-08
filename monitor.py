import requests
import json


def main():
    errors = []
    filename = 'sites.json'
    with open(filename) as fh:
        config = json.load(fh)
    for site in config["sites"]:
        url = site["url"]
        print(url)
        if 'enabled' in site and not site['enabled']:
            continue

        resp = requests.get(url, allow_redirects=False)
        print(resp.status_code)
        print(resp.headers)
        if resp.status_code != site["status_code"]:
            errors.append(f'URL {url} expected {site["status_code"]} received {resp.status_code}')

        if 'headers' in site:
            for header in site["headers"]:
                if header in resp.headers:
                    if site["headers"][header] != resp.headers[header]:
                        errors.append('URL {url} is expected to have header {header}={site["headers"][header]} but it is {resp.header[header]}')
                else:
                    errors.append(f'URL {url} is expected to have a header "{header}" but it is missing')

        if 'html_contains' in site:
            if site['html_contains'] not in resp.content.decode('utf-8'):
                errors.append(f'URL {url} expected some html_content but did not receive it')

    if errors:
        for error in errors:
            print(error)
        exit(1)
    else:
        print("Everything is fine")
        exit(0)
if __name__ == '__main__':
    main()