from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

logging.basicConfig(filename='logs/api.log', level=logging.INFO)

@app.route("/data")
def data():
    logging.info("endpoint /data accessed")
    return jsonify({"status": "ok", "data": "public data"})

@app.route("/admin")
def admin():
    logging.info("admin endpoint accessed")
    return jsonify({"status": "forbidden"}), 403

app.run(host="0.0.0.0", port=5000)