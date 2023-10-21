import random
from typing import Optional, Any
import requests
import time

from aptos_sdk import ed25519
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.client import RestClient, ResourceNotFound, ApiError
from aptos_sdk.account import Account
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionPayload,
    SignedTransaction,
)
from aptos_sdk.type_tag import TypeTag, StructTag

from data.models import TokenAmount, ResourceType, Tokens, Token
from data.config import logger, PROXIS_PATH
from utils.utils import get_explorer_hash_link
from utils.files_utils import select_random_proxy


class AptosClient(RestClient):
    node_url = 'https://fullnode.mainnet.aptoslabs.com/v1'

    def __init__(self, private_key: str, proxy: Optional[str] = None, check_proxy: bool = True):
        super().__init__(AptosClient.node_url)
        self.private_key = private_key
        self.signer = Account.load_key(self.private_key)
        self.address = AccountAddress.from_key(ed25519.PrivateKey.from_hex(private_key).public_key()).hex()
        self.proxy = proxy

        if check_proxy:
            decimals = self.get_decimals(token=Tokens.APT)
            while decimals == 0:
                self.proxy = select_random_proxy(path=PROXIS_PATH)
                decimals = self.get_decimals(token=Tokens.APT)

        self.client_config.max_gas_amount = 100000

    def get_coin_data(self, token: Token) -> Optional[dict]:
        try:
            coin_store_address = f'{ResourceType.store}<{token.address}>'
            coin_data = self.account_resource(account_address=self.signer.address(), resource_type=coin_store_address)
            return coin_data
        except:
            try:
                self.register(token)
            except Exception as e:
                logger.error(f'Get coin data error: {str(e)}')
        return {}

    def get_decimals(self, token: Token) -> int:
        try:
            token_address = AccountAddress.from_hex(token.address.split('::')[0])
            coin_info = self.account_resource(
                account_address=token_address, resource_type=f'{ResourceType.info}<{token.address}>')
            return coin_info['data']['decimals']
        except Exception as e:
            # logger.error(f'Get coin info error: {str(e)}')
            return 0

    def get_balance(self, token: Optional[Token] = None) -> Optional[TokenAmount]:
        if not token:
            token = Tokens.APT
        coin_data = self.get_coin_data(token)
        balance = coin_data.get('data', {}).get('coin', {}).get('value')
        decimals = self.get_decimals(token=token)

        if balance is not None:
            return TokenAmount(amount=int(balance), decimals=decimals, wei=True)
        return TokenAmount(amount=0, decimals=decimals, wei=True)

    def get_domain_name_dict(self, account_address: Optional[str] = None, random_proxy: bool = False) -> Optional[dict]:
        if not account_address:
            account_address = self.address
        url = f'https://www.aptosnames.com/api/mainnet/v1/primary-name/{account_address}'
        if random_proxy:
            self.proxy = select_random_proxy(path=PROXIS_PATH)
        try:
            if self.proxy is None:
                response = self.client.get(url)
            else:
                response = requests.get(url, proxies={'https': f'http://{self.proxy}'})
            return response.json()
        except requests.exceptions.ProxyError:
            if random_proxy:
                return None
            return self.get_domain_name_dict(account_address=account_address, random_proxy=True)

    def register(self, token: Token) -> None:
        try:
            payload = EntryFunction.natural(
                '0x1::managed_coin',
                'register',
                [TypeTag(StructTag.from_str(token.address))],
                [],
            )
            signed_transaction = self.create_bcs_signed_transaction(
                sender=self.signer, payload=TransactionPayload(payload)
            )
            tx = self.submit_bcs_transaction(signed_transaction)
            self.wait_for_transaction(tx)
            logger.success(f'Token \'{token}\' is registered: {get_explorer_hash_link(tx)}')
            time.sleep(random.randint(10, 30))
        except Exception as e:
            if 'account_not_found' in str(e):
                logger.error(f'{self.address} | Account wasn\'t activated, send gas to activate this account')
            else:
                logger.error(f'Register token error: {str(e)}')

    # ------------------------------ функции из основной библиотеки с поддержкой прокси ------------------------------
    def account_resource(
            self,
            resource_type: str,
            account_address: Optional[AccountAddress] = None,
            ledger_version: int = None
    ) -> dict[str, Any]:
        if not account_address:
            account_address = self.address
        if not ledger_version:
            request = f'{self.base_url}/accounts/{account_address}/resource/{resource_type}'
        else:
            request = f'{self.base_url}/accounts/{account_address}/resource/{resource_type}' \
                      f'?ledger_version={ledger_version}'

        if self.proxy is None:
            response = self.client.get(request)
        else:
            response = requests.get(
                request, proxies={'https': f'http://{self.proxy}'})

        if response.status_code == 404:
            raise ResourceNotFound(resource_type, resource_type)
        if response.status_code >= 400:
            raise ApiError(
                f'{response.text} - {account_address}', response.status_code)
        return response.json()

    def submit_bcs_transaction(self, signed_transaction: SignedTransaction) -> str:
        headers = {"Content-Type": "application/x.aptos.signed_transaction+bcs"}

        if self.proxy is None:
            response = self.client.post(
                f"{self.base_url}/transactions",
                headers=headers,
                data=signed_transaction.bytes(),
            )
        else:
            response = requests.post(
                f"{self.base_url}/transactions",
                headers=headers,
                data=signed_transaction.bytes(),
                proxies={"https": f"http://{self.proxy}"}
            )

        if response.status_code >= 400:
            raise ApiError(response.text, response.status_code)
        return response.json()["hash"]

    def wait_for_transaction(self, txn_hash: str) -> None:
        count = 0
        while self.transaction_pending(txn_hash):
            assert (
                    count < self.client_config.transaction_wait_in_seconds
            ), f"transaction {txn_hash} timed out"
            time.sleep(1)
            count += 1

        if self.proxy is None:
            response = self.client.get(
                f"{self.base_url}/transactions/by_hash/{txn_hash}")
        else:
            response = requests.get(
                f"{self.base_url}/transactions/by_hash/{txn_hash}",
                proxies={"https": f"http://{self.proxy}"}
            )
        assert (
                "success" in response.json() and response.json()["success"]
        ), f"{response.text} - {txn_hash}"

    def transaction_pending(self, txn_hash: str) -> bool:
        if self.proxy is None:
            response = self.client.get(
                f"{self.base_url}/transactions/by_hash/{txn_hash}")
        else:
            response = requests.get(
                f"{self.base_url}/transactions/by_hash/{txn_hash}",
                proxies={"https": f"http://{self.proxy}"}
            )
        if response.status_code == 404:
            return True
        if response.status_code >= 400:
            raise ApiError(response.text, response.status_code)
        return response.json()["type"] == "pending_transaction"
