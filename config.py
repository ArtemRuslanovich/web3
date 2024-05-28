import os
from dotenv import load_dotenv

load_dotenv()

ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
ARBISCAN_API_KEY = os.getenv('ARBISCAN_API_KEY')

alchemy_url = f'https://eth-mainnet.alchemyapi.io/v2/{ALCHEMY_API_KEY}'