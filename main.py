import requests
from flask import Flask, jsonify, render_template, request
from web3 import Web3


app = Flask(__name__)

def read_api_key(filename='keys.txt'):
    with open(filename, 'r') as file:
        return file.read().strip()

ARBISCAN_API_KEY = read_api_key()
alchemy_api_key = 'JHIR3eEJvo1ttf9lJsy7f7V4gt5nbJao'

# Подключалка к Эфириуму через Alchemy
alchemy_url = f'https://eth-mainnet.alchemyapi.io/v2/{alchemy_api_key}'
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
    return float(data['result']['ethusd'])

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
        address = request.form['address']
        balance = web3.eth.get_balance(address)
        eth_balance = web3.fromWei(balance, 'ether')
        return jsonify({'address': address, 'balance': eth_balance}), 200
    except ValueError as e:
        return jsonify({'error': 'Invalid Balance addres'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/transaction', methods=['POST'])
# проверка хеша транзы
def transaction():
    try:
        tx_hash = request.form['tx_hash']
        tx = web3.eth.get_transaction(tx_hash)
        return jsonify({'transaction': tx}), 200
    except ValueError as e:
        print('Invalid transaction hash:', e)
        return jsonify({'error': 'Invalid transaction hash'}), 400
    except Exception as e:
        print('Error fetching the transaction:', e)
        return jsonify({'error': 'Error fetching transaction'}), 500

if __name__ == '__main__':
    app.run(debug=True)
    check_connection()