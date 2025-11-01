# Flask API for AQI Prediction
# TODO: Implement API endpoints

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "AQI Prediction API"})

if __name__ == '__main__':
    app.run(debug=True)
