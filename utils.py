import requests
from web3 import Web3
from decimal import Decimal
import json
from config import ALCHEMY_API_KEY, ARBISCAN_API_KEY, uniswap_router_address, alchemy_url

web3 = Web3(Web3.HTTPProvider(alchemy_url))

# проверка подключения
def check_connection():
    try:
        web3 = Web3(Web3.HTTPProvider(alchemy_url))
        print("Connected to Alchemy successfully!")
    except Exception as e:
        print("Failed to connect to Alchemy:", e)

# получение цены eth к usd
def get_eth_price(ARBISCAN_API_KEY):
    url = f"https://api.arbiscan.io/api"
    params = {
        'module': 'stats',
        'action': 'ethprice',
        'apikey': ARBISCAN_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return Decimal(data['result']['ethusd'])

with open('uniswap_v2_router_abi.json', 'r') as abi_file:
    uniswap_router_abi = json.load(abi_file)

uniswap_router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

# Создание объекта контракта
uniswap_router = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

# для определения, сколько токенов получится в результате свапа
def get_amount_out(amount_in, token_in, token_out): # количество входных токенов, адрес входного токена, адрес выходного токена
    amount_in_wei = web3.to_wei(amount_in, 'ether')
    amounts_out = uniswap_router.functions.getAmountsOut( # возвращает массив выходных токенов по указанному пути
        amount_in_wei,
        [web3.toChecksumAddress(token_in), web3.toChecksumAddress(token_out)]
    ).call()
    amount_out_wei = amounts_out[-1] # последний элемент из массива amounts_out - количество выходных токенов в Wei.
    return web3.from_wei(amount_out_wei, 'ether')

# Функция свапа токенов
def swap_tokens(amount_in, amount_out_min, token_in, token_out, wallet_address, private_key):
    nonce = web3.eth.getTransactionCount(wallet_address) # уникальное число для каждой транзакции, шоб повторно не срабатывало
    deadline = web3.eth.getBlock('latest')['timestamp'] + 1000  # 1000 секунд от текущего времени, до которого транзакция должна быть включена в блокчейн

    transaction = uniswap_router.functions.swapExactTokensForTokens( # функция контракта Uniswap Router для обмена токенов
        web3.to_wei(amount_in, 'ether'),
        web3.to_wei(amount_out_min, 'ether'),
        [web3.toChecksumAddress(token_in), web3.toChecksumAddress(token_out)],
        wallet_address,
        deadline
    ).buildTransaction({ # метод, который подготавливает транзакцию для отправки, указывая отправителя, газ, цену газа и nonce
        'from': wallet_address,
        'gas': 2000000,
        'gasPrice': web3.toWei('5', 'gwei'),
        'nonce': nonce,
    })

    gas_estimate = web3.eth.estimateGas(transaction) # оценка количества газа, необходимого для выполнения транзакции.
    transaction['gas'] = gas_estimate # обновление gas в buildTransaction

    signed_tx = web3.eth.account.signTransaction(transaction, private_key) # подписание транзы
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction) # отправка транзы, rawTrans - для формата, который может быть передан в сеть

    return web3.toHex(tx_hash)