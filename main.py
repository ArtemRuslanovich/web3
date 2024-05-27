from flask import Flask, render_template
import requests
from keys import ARBISCAN_API_KEY

app = Flask(__name__)

ETHERSCAN_API_URL = f'https://api.arbiscan.io/api?module=stats&action=ethprice&apikey={ARBISCAN_API_KEY}'

@app.route('/')
def index():
    response = requests.get(ETHERSCAN_API_URL)
    data = response.json()
    eth_price = data['result']['ethusd']
    return render_template('index.html', price=eth_price)

if __name__ == '__main__':
    app.run(debug=True)