import random
import time

from loguru import logger

from client import AptosClient
from utils.files_utils import read_lines
from data import config
from tasks.domain_names import DomainNames
from data.models import Settings


def start_script():
    settings = Settings()
    private_keys = read_lines(path=config.PRIVATE_KEYS_PATH)
    proxies = read_lines(path=config.PROXIS_PATH)
    if not proxies:
        logger.critical(f'Please add proxy to {config.PROXIS_PATH}')
        return
    delta = len(private_keys) - len(proxies)
    if delta > 0:
        proxies *= int(len(private_keys) / len(proxies)) + 1

    while private_keys:
        i = random.randint(0, len(private_keys) - 1)
        private_key = private_keys[i]
        proxy = proxies[i]
        aptos_client = AptosClient(private_key=private_key, proxy=proxy)
        domain_name = DomainNames(aptos_client=aptos_client)
        logger.info(f'{len(private_keys)} wallets left | current wallet address: {aptos_client.address}')

        domain_name_dict = aptos_client.get_domain_name_dict(account_address=aptos_client.address)

        if domain_name_dict is not None and domain_name_dict.get('name'):
            logger.info(f'current_domain_name: {domain_name_dict.get("name")}')
            print()
            private_keys.pop(i)
            proxies.pop(i)
            continue

        status = domain_name.mint_domain_name()

        if 'Failed' in status:
            logger.error(f'({aptos_client.address}) Can not mint domain name: {status}')
            print()
            continue

        logger.success(f'({aptos_client.address}) Line drawn')
        print()
        private_keys.pop(i)
        proxies.pop(i)
        time.sleep(random.randint(settings.sleep_time.from_, settings.sleep_time.to_))


if __name__ == '__main__':
    start_script()
