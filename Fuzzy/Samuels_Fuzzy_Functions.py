"""
Sam's part: how to get to an event, and the final ranking that puts everyone's scores together.
app.py calls rank_events() with the answers from the page.
"""

import math

<<<<<<< Updated upstream
if __package__:
    from Fuzzy.event_data import EVENTS, SAMPLE_USER, RATING_AGE
else:
    from event_data import EVENTS, SAMPLE_USER, RATING_AGE
=======
# The events come from the shared data file
try:
    from Fuzzy.event_data import EVENTS     # when app.py uses this file
except ImportError:
    from event_data import EVENTS           # when this file is run on its own
>>>>>>> Stashed changes


# speed in km/h, wait in minutes, hassle = effort just for using it, effort per minute of travel
MODES = {
    "walk":   {"speed": 5,  "wait": 0,  "hassle": 0.0, "effort_per_min": 0.15},
    "bike":   {"speed": 15, "wait": 2,  "hassle": 0.5, "effort_per_min": 0.12},
    "public": {"speed": 25, "wait": 10, "hassle": 1.5, "effort_per_min": 0.05},
    "car":    {"speed": 35, "wait": 10, "hassle": 2.0, "effort_per_min": 0.04},
    "taxi":   {"speed": 35, "wait": 8,  "hassle": 1.5, "effort_per_min": 0.02},
}

DETOUR = 1.3                # roads aren't straight
CHF_PER_EFFORT_POINT = 5    # CHF 5 feels about as bad as 1 point of effort
BERN = {"name": "Bern HB", "lat": 46.9490, "lon": 7.4391}

# how special an event is: the more special, the less a long trip matters
SPECIAL = {"weekly": 0.1, "monthly": 0.3, "seasonal": 0.5, "once": 0.7, "yearly": 1.0}

<<<<<<< Updated upstream

def distance_km(origin, event):
    if "lat" not in event:
        return event["distance_km"]
    dy = (event["lat"] - origin["lat"]) * 111
    dx = (event["lon"] - origin["lon"]) * 111 * math.cos(math.radians(origin["lat"]))
    return math.sqrt(dx * dx + dy * dy) * DETOUR


def cost_per_person(mode, km, group_size):
    if mode == "public":
        return 3.0 if km <= 5 else 3.0 + 0.30 * km
    if mode == "taxi":
        taxis = math.ceil(group_size / 4)
        return taxis * (6.80 + 3.80 * km) / group_size
    if mode == "car":
        cars = math.ceil(group_size / 5)
        return cars * (0.20 * km + 5) / group_size
    return 0.0   # walk, bike
=======
# Event fields this file uses (in event_data.py):
#   lat, lon      where it is (if missing, distance_km is used instead)
#   price         ticket price per person in CHF
#   repeats       how often it happens -> how special it is (0 = not special, 1 = very)
SPECIAL = {"weekly": 0.1, "monthly": 0.3, "seasonal": 0.5, "once": 0.7, "yearly": 1.0}
>>>>>>> Stashed changes


def plan_trip(origin, modes, group_size, event):
    km = distance_km(origin, event)

    options = []
    for mode in modes:
        if mode not in MODES:
            continue
        m = MODES[mode]
        minutes = m["wait"] + km / m["speed"] * 60
        options.append({
            "mode": mode,
            "minutes": round(minutes),
            "cost_each": round(cost_per_person(mode, km, group_size), 2),
            "effort": round(m["hassle"] + minutes * m["effort_per_min"], 1),
        })

    # easiest way there, counting money as effort too
    options.sort(key=lambda o: o["effort"] + o["cost_each"] / CHF_PER_EFFORT_POINT)
    best = options[0]

    return {
        "km": round(km, 1),
        "mode": best["mode"],
        "minutes": best["minutes"],
        "cost_each": best["cost_each"],
        "effort": best["effort"],
        "options": options,
    }


def trip_score(trip, energy_level, event):
    energy = (energy_level - 1) * 2.5   # energy 1-5 -> 0-10, same scale as effort

    if trip["effort"] <= energy:
        match = 1.0
    else:
        match = 2 ** -(trip["effort"] - energy)   # halves for every point too hard

    special = SPECIAL.get(event.get("repeats"), 0)
    return match ** (1 - special)


# imported down here because Fiona's file imports plan_trip from this one
if __package__:
    from Fuzzy import fionas_part, marlenes_part
else:
    import fionas_part, marlenes_part


def read_curve(curve):
    return float(curve[0])


def time_score(event, times):
    fits = marlenes_part.time_membership(event["start"])
    return max(fits[t] for t in times if t in fits)


def keyword_score(event, keywords, importance):
    beta = importance / 10
    scores = []
    for k in keywords:
        alpha = 1 if k in event["keywords"] else 0
        scores.append(marlenes_part.keyword_membership(alpha, beta))
    return max(scores)


def geometric_mean(scores):
    if not scores:
        return 1.0
    product = 1.0
    for s in scores:
        product *= s
    return product ** (1 / len(scores))


def score_event(event, answers, trip):
    energy = answers.get("energy") or {"level": 3, "word": "okay", "importance": 5}
    money = answers.get("money") or {"min": 0, "max": 200, "importance": 5}
    group = answers.get("group") or {"size": 1, "importance": 5}
    kids = answers.get("kids_ok")
    times = answers.get("times") or []
    keywords = answers.get("keywords") or []
    keyword_importance = answers.get("keyword_importance", 5)
    at = fionas_part.at

    # a slider at 0 means "doesn't matter", so that score is left out
    scores = {}
    if times:
        scores["time"] = time_score(event, times)

    scores["trip"] = trip_score(trip, energy["level"], event)

    if energy["importance"] > 0:
        scores["vibe"] = marlenes_part.energy_membership(energy["word"], energy["importance"], event["energy"])

    if money["importance"] > 0:
        total = event["price"] + trip["cost_each"]
        curve = fionas_part.money_membership(money["max"], money["importance"], money["min"], x=at(total))
        scores["price"] = read_curve(curve)

    if group["importance"] > 0:
        curve = fionas_part.group_membership(group["size"], group["importance"], x=at(event["capacity"]))
        scores["group"] = read_curve(curve)

    # movie ratings turned into ages (PG -> 6, PG-13 -> 12, ...) for Fiona's kids function
    if kids and kids["importance"] > 0:
        event_age = RATING_AGE[event["rating"]]
        allowed_age = RATING_AGE[kids["rating"]]
        curve = fionas_part.kids_ok_membership(event_age, kids["importance"], x=at(allowed_age))
        scores["kids"] = read_curve(curve)

    if keywords and keyword_importance > 0:
        scores["keywords"] = keyword_score(event, keywords, keyword_importance)

    return scores


def rank_events(answers, events=EVENTS):
    origin = answers.get("from") or BERN
    modes = answers.get("modes") or ["walk"]
    group_size = (answers.get("group") or {}).get("size", 1)

    results = []
    for event in events:
        if not marlenes_part.date_passes(event["date"], answers.get("dateFrom"), answers.get("dateTo")):
            continue

        trip = plan_trip(origin, modes, group_size, event)
<<<<<<< Updated upstream
        scores = score_event(event, answers, trip)
=======

        # 3. Energy match. A box up to my energy level, then halves for every
        #    point the trip is harder than that, but never reaches 0.
        if trip["effort"] <= energy:
            energy_match = 1.0
        else:
            energy_match = 2 ** -(trip["effort"] - energy)

        # 4. Special events. The more special the event, the less the energy match counts.
        #    special 0 -> score stays as it is, special 1 -> score becomes 1.
        special = SPECIAL.get(event.get("repeats"), 0)
        trip_score = energy_match ** (1 - special)

        # 5. Money (placeholder until Fiona's money function): ticket + travel.
        #    Fine up to the max price, then halves for every CHF 10 over.
        total_cost = event["price"] + trip["cost_each"]
        if total_cost <= price_max:
            money_score = 1.0
        else:
            money_score = 2 ** -((total_cost - price_max) / 10)

        # 6. Teammates' scores go here when they're ready, e.g.
        #    time_score = ...      (Marlene)
        #    group_score = ...     (Fiona)

        # 7. Final score: an event is only as good as its weakest part (fuzzy AND)
        score = min(trip_score, money_score)
>>>>>>> Stashed changes

        results.append({
            "name": event["name"],
            "venue": event.get("venue", ""),
            "date": event["date"],
            "start": event["start"],
            "price": event["price"],
            "rating": event["rating"],
            "score": round(geometric_mean(list(scores.values())), 2),
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "total_cost": round(event["price"] + trip["cost_each"], 2),
            "trip": trip,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


if __name__ == "__main__":
    for r in rank_events(SAMPLE_USER):
        why = "  ".join(f"{k} {v:.2f}" for k, v in r["scores"].items())
        print(f"{r['score']:.2f}  {r['name'][:30]:<30} {r['date']}  {why}")
