#!/usr/bin/env python
import requests
import json
import logging
import time
import socket
import glob
import sys
import dns.resolver

# TODO: check TXT and CNAME records as well. Monitor the whole DNS configuration?
# TODO: Check IPv6 resolutions as well.
# TODO: http multi-step monitorig with username/password?

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    sh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)-10s - %(message)s'))
    logger.addHandler(sh)
    return logger

class Monitor:
    def __init__(self):
        self.errors = []
        self.logger = setup_logger()

    def save_error(self, text):
        self.logger.error(text)
        self.errors.append(text)

    def check_mx(self, site):
        domain = site['mx']
        self.logger.info(f"Domain: {domain}")
        try:
            records = list(map(lambda rec: str(rec.exchange), dns.resolver.query(domain, 'MX')))
            if sorted(records) != sorted(site["ips"]):
                self.save_error(f"Domain {domain} Expected IPS for MX: {site['ips']}  received: {records}")
        except dns.resolver.NoAnswer as err:
            self.save_error(f"Domain {domain} Could not find MX record")

    def check_host(self, site):
        host = site['host']
        self.logger.info(f"Host: {host}")

        if site["ips"] == "github":
            site["ips"] = [
                "185.199.108.153",
                "185.199.109.153",
                "185.199.110.153",
                "185.199.111.153"
            ]
        try:
            hostname, aliaslist, ip_addresses = socket.gethostbyname_ex(host)
            self.logger.info(f"hostname: {hostname} ip_addresses={ip_addresses}")
            if set(ip_addresses) != set(site["ips"]):
                self.save_error(f"Host {host} Expected IPS: {site['ips']}  received: {ip_addresses}")
        except Exception as err:
            self.save_error(f"Host {host} Expection {err} of type {err.__class__.__name__} received")

    def check_url(self, site):
        url = site["url"]
        logger = self.logger
        logger.info(f"URL: {url}")

        start = time.time()
        try:
            resp = requests.get(url, allow_redirects=False)
        except Exception as err:
            self.save_error(f'URL {url} got an exception {err}')
            return
        finally:
            end = time.time()
            logger.info(f"elaspsed time: {end - start}")

        logger.info(f"status_code: {resp.status_code}")
        logger.info(f"headers: {resp.headers}")
        if resp.status_code != site["status_code"]:
            self.save_error(f'URL {url} expected {site["status_code"]} received {resp.status_code}')

        if 'headers' in site:
            for header in site["headers"]:
                if header in resp.headers:
                    if site["headers"][header] != resp.headers[header]:
                        self.save_error(
                            f'URL {url} is expected to have header {header}={site["headers"][header]} but it is {resp.headers[header]}')
                else:
                    self.save_error(f'URL {url} is expected to have a header "{header}" but it is missing')

        if 'html_contains' in site:
            if site['html_contains'] not in resp.content.decode('utf-8'):
                self.save_error(f'''URL {url} expected html_content '{site['html_contains']}' but did not receive it.''')

    def main(self):
        start_process = time.time()

        if len(sys.argv) == 1:
            exit(f"Usage: {sys.argv[0]} JSON_FILEs")

        filenames = sys.argv[1:]
        for filename in filenames:
            self.logger.info(f"Processing {filename}")
            try:
                with open(filename) as fh:
                    config = json.load(fh)
            except Exception as err:
                self.save_error(f'Exception {err} while reading config file {filename}')
            try:
                for site in config["sites"]:

                    if 'enabled' in site and not site['enabled']:
                        continue
                    if 'host' in site:
                        self.check_host(site)
                    if 'mx' in site:
                        self.check_mx(site)
                    if 'url' in site:
                        self.check_url(site)
            except Exception as err:
                self.save_error(f'Exception {err} while processing site {site} from file {filename}')

        end_process = time.time()

        self.logger.info(f"Elapsed time: {end_process - start_process}")
        self.logger.info(f"--------------------------")
        if self.errors:
            for error in self.errors:
                self.logger.error(error)
            return 1
        else:
            self.logger.info("Everything is fine")
            return 0


if __name__ == '__main__':
    code = Monitor().main()
    exit(code)
