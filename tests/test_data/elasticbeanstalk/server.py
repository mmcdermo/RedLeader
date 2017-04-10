from flask import Flask, jsonify, request, abort, make_response

app = Flask(__name__)

@app.route('/api/test/')
def algorithms():
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
