import requests
import json


def main():
    errors = []
    filename = 'sites.json'
    with open(filename) as fh:
        config = json.load(fh)
    for site in config["sites"]:
        print(site["url"])
        resp = requests.get(site["url"])
        if resp.status_code != site["status_code"]:
            errors.append(f'URL {site["url"]} expected {site["status_code"]} received {resp.status_code}')
        if 'html_contains' in site:
            if site['html_contains'] not in resp.content.decode('utf-8'):
                errors.append(f'URL {site["url"]} expected some html_content but did not receive it')

    if errors:
        for error in errors:
            print(error)
        exit(1)
    else:
        print("Everything is fine")
        exit(0)
if __name__ == '__main__':
    main()