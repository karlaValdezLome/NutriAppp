from flask import Flask

app = Flask(__name__)

@app.route('/index.html')
def home():
    return index.html

if __name__ == '__main__':
    app.run(debug=True)