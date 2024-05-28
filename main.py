import requests
from flask import Flask, jsonify, render_template, request
from web3 import Web3
from decimal import Decimal
from dotenv import load_dotenv
import os
import json


app = Flask(__name__)
load_dotenv()


ALCHEMY_API_KEY = os.getenv('alchemy_api_key')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')
ARBISCAN_API_KEY = os.getenv('ARBISCAN_API_KEY')

# Подключалка к Эфириуму через Alchemy
alchemy_url = f'https://eth-mainnet.alchemyapi.io/v2/{ALCHEMY_API_KEY}'
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/price', methods=['GET'])
def price():
    try:
        price = get_eth_price(ARBISCAN_API_KEY)
        return jsonify({'Ethereum Price (USD)': price}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/balance', methods=['POST'])
# проверка баланса кошеля
def balance():
    try:
        request_data = request.get_json()
        address = request_data['address']
        wallet_address = web3.to_checksum_address(address)
        balance = web3.eth.get_balance(wallet_address)
        eth_balance = web3.from_wei(balance, 'ether')
        return jsonify({'address': wallet_address, 'balance': eth_balance}), 200
    except ValueError as e:
        print('Invalid transaction hash:', e)
        return jsonify({'error': 'Invalid Balance addres'}), 400
    except Exception as e:
        print('Error fetching the transaction:', e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/transaction', methods=['POST'])
# проверка хеша транзы
def transaction():
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({'error': 'Missing request data'}), 400
        
        tx_hash = request_data.get('tx_hash')
        if not tx_hash:
            return jsonify({'error': 'Missing transaction hash in request data'}), 400
        
        try:
            tx = web3.eth.get_transaction(tx_hash)
        except Exception as e:
            print('Error fetching transaction from Web3:', e)
            return jsonify({'error': 'Invalid transaction hash or error fetching transaction from Web3'}), 400
        
        tx_value_eth = Web3.from_wei(tx.value, 'ether') # перевод из wei в ETH
        eth_price_usd = get_eth_price(ARBISCAN_API_KEY) # call the function to get the current ETH price
        tx_value_usd = tx_value_eth * eth_price_usd # умножается на текущий курс ETH/USD для получения значения в долларах
        
        tx_data = {
            'tx_hash': tx.hash.hex(), # образует в 16ричную строчку
            'blockNumber': tx.blockNumber,
            'value': f"{tx_value_eth} ETH (${tx_value_usd:.2f})",
            'from': tx['from'],
            'to': tx['to']
        }

        if tx.blockNumber is None:
            return jsonify({'error': 'Транзакция еще не включена в блок'}), 400

        return jsonify({'transaction': tx_data}), 200

    except ValueError as e:
        print('Invalid transaction hash:', e)
        return jsonify({'error': 'Invalid transaction hash'}), 400
    except Exception as e:
        print('Error fetching the transaction:', e)
        return jsonify({'error': 'Error fetching transaction'}), 500


with open('uniswap_v2_router_abi.json', 'r') as abi_file:
    uniswap_router_abi = json.load(abi_file)

uniswap_router_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

# Создание объекта контракта
uniswap_router = web3.eth.contract(address=uniswap_router_address, abi=uniswap_router_abi)

# Функция свапа токенов
def swap_tokens(amount_in, amount_out_min, token_in, token_out, wallet_address, private_key):
    nonce = web3.eth.getTransactionCount(wallet_address)
    deadline = web3.eth.getBlock('latest')['timestamp'] + 1000  # 1000 секунд от текущего времени

    transaction = uniswap_router.functions.swapExactTokensForTokens(
        web3.to_wei(amount_in, 'ether'),
        web3.to_wei(amount_out_min, 'ether'),
        [web3.toChecksumAddress(token_in), web3.toChecksumAddress(token_out)],
        wallet_address,
        deadline
    ).buildTransaction({
        'from': wallet_address,
        'gas': 2000000,
        'gasPrice': web3.toWei('5', 'gwei'),
        'nonce': nonce,
    })

    signed_tx = web3.eth.account.signTransaction(transaction, private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    return web3.toHex(tx_hash)

# Маршрут для свапа токенов
@app.route('/swap', methods=['POST'])
def swap():
    try:
        data = request.get_json()
        amount_in = data.get('amount_in')
        amount_out_min = data.get('amount_out_min')
        token_in = data.get('token_in')
        token_out = data.get('token_out')
        
        wallet_address = os.getenv('WALLET_ADDRESS')
        private_key = os.getenv('PRIVATE_KEY')
        
        if not all([amount_in, amount_out_min, token_in, token_out]):
            return jsonify({'error': 'Missing parameters'}), 400
        
        tx_hash = swap_tokens(amount_in, amount_out_min, token_in, token_out, wallet_address, private_key)
        return jsonify({'transaction_hash': tx_hash}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
    check_connection()