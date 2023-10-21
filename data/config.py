from loguru import logger
import os
import sys
from pathlib import Path


if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()

FILES_DIR = os.path.join(ROOT_DIR, 'files')

PRIVATE_KEYS_PATH = os.path.join(FILES_DIR, 'private_keys.txt')
PROXIS_PATH = os.path.join(FILES_DIR, 'proxies.txt')
SETTINGS_PATH = os.path.join(FILES_DIR, 'settings.json')
DEBUG_PATH = os.path.join(FILES_DIR, 'debug.log')

logger.add(f'{DEBUG_PATH}', format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}', level='DEBUG')
