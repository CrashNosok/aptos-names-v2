from typing import Union
from dataclasses import dataclass
from decimal import Decimal

from utils.files_utils import read_json
from data.config import SETTINGS_PATH


class ResourceType:
    # https://aptos.dev/integration/aptos-api/
    info = '0x1::coin::CoinInfo'
    store = '0x1::coin::CoinStore'
    token_store = '0x3::token::TokenStore'


class Token:
    def __init__(self, name: str, address: str):
        self.name = name
        self.address = address

    def __str__(self) -> str:
        return f'{self.name}'


class Tokens:
    APT = Token(name='AptosCoin', address='0x1::aptos_coin::AptosCoin')


class AptosNames:
    router = '0x867ed1f6bf916171b1de3ee92849b8978b7d1b9e0a8cc982a3d19d535dfd9c0c'
    script = '0x867ed1f6bf916171b1de3ee92849b8978b7d1b9e0a8cc982a3d19d535dfd9c0c::router'
    function = 'register_domain'


class AutoRepr:
    def __repr__(self) -> str:
        values = ('{}={!r}'.format(key, value) for key, value in vars(self).items())
        return '{}({})'.format(self.__class__.__name__, ', '.join(values))


class Singleton:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls)

        return cls._instances[cls]


@dataclass
class FromTo:
    from_: Union[int, float]
    to_: Union[int, float]


class Settings(Singleton, AutoRepr):
    def __init__(self):
        json = read_json(path=SETTINGS_PATH)

        self.check_proxy: bool = json['check_proxy']
        self.sleep_time: FromTo = FromTo(from_=json['sleep_time']['from'], to_=json['sleep_time']['to'])


class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        if wei:
            self.Wei: int = amount
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals

    def __str__(self):
        return f'{self.Ether}'
