from flask import Flask, jsonify, render_template, request
from utils import check_connection, get_eth_price, get_amount_out, swap_tokens, web3
from config import WALLET_ADDRESS, PRIVATE_KEY, ARBISCAN_API_KEY
from web3 import Web3
import logging


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



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

# Маршрут для свапа токенов
@app.route('/swap', methods=['POST'])
def swap():
    try:
        data = request.get_json()
        amount_in = data.get('amount_in')
        amount_out_min = data.get('amount_out_min')
        token_in = data.get('token_in')
        token_out = data.get('token_out')
        
        if not all([amount_in, amount_out_min, token_in, token_out]):
            return jsonify({'error': 'Missing parameters'}), 400
        
        tx_hash = swap_tokens(amount_in, amount_out_min, token_in, token_out, WALLET_ADDRESS, PRIVATE_KEY)
        return jsonify({'transaction_hash': tx_hash}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_amount_out', methods=['POST'])
def get_amount_out_route():
    try:
        data = request.get_json()
        amount_in = data.get('amount_in')
        token_in = data.get('token_in')
        token_out = data.get('token_out')

        if not all([amount_in, token_in, token_out]):
            logger.error("Отсутствуют параметры в запросе")
            return jsonify({'error': 'Отсутствуют параметры'}), 400
        
        amount_out = get_amount_out(amount_in, token_in, token_out)
        return jsonify({'amount_out': str(amount_out)}), 200

    except Exception as e:
        logger.exception("Ошибка сервера")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    check_connection()
    app.run(debug=True)