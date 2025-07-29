from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    return "Webhook funcionando!"

if __name__ == '__main__':
    print("Iniciando Flask de prueba...")
    app.run(host='0.0.0.0', port=8888, debug=False)
