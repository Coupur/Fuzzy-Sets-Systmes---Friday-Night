from flask import Flask, request, jsonify, send_from_directory
from Fuzzy import fionas_part
from Fuzzy.event_data import EVENTS

app = Flask(__name__, static_folder="event-search")

EVENTS_BY_NAME = {e["name"]: e for e in EVENTS}

# Fiona's score names -> the names the results page uses
SCORE_NAMES = {"time": "time", "distance": "trip", "energy": "vibe", "money": "price",
               "group size": "group", "kids_ok": "kids", "keywords": "keywords"}


def for_page(row):
    event = EVENTS_BY_NAME[row["event"]]
    return {
        "name": event["name"],
        "venue": event["venue"],
        "date": event["date"],
        "start": event["start"],
        "price": event["price"],
        "rating": event["rating"],
        "score": round(row["relevance"], 2),
        "scores": {SCORE_NAMES[k]: round(row[k], 2) for k in SCORE_NAMES if k in row},
        "total_cost": row["total_cost"],
        "trip": row["trip"],
    }


@app.route("/")
def home():
    return send_from_directory("event-search", "filters.html")


@app.route("/api/search", methods=["POST"])
def search():
    answers = request.get_json()
    rows = fionas_part.rank(answers)
    return jsonify([for_page(r) for r in rows])


if __name__ == "__main__":
    app.run(debug=True)
