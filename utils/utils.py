from data.config import logger


def get_explorer_hash_link(tx_hash: str):
    try:
        return f"https://explorer.aptoslabs.com/txn/{tx_hash}?network=mainnet"
    except Exception as e:
        logger.error(f"Ge"
                     f"t explorer hash link error: {str(e)}")
