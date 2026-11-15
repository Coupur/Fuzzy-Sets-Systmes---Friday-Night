from flask import Flask, request, jsonify, send_from_directory
from Fuzzy import Samuels_Fuzzy_Functions

app = Flask(__name__, static_folder="event-search")

@app.route("/")
def home():
    return send_from_directory("event-search", "filters.html")

@app.route("/api/search", methods=["POST"])
def search():
    answers = request.get_json()          # what the user picked
    results = Samuels_Fuzzy_Functions.rank_events(answers)   # the fuzzy part
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
