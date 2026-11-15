"""
Sam's part: getting to the event, and ranking the events.

How one Search click flows through the code:

    filters.html   getFilters()        collects the answers -> JSON
    app.py         /api/search         receives the JSON, calls rank_events()
    this file      rank_events()       for every event:
                       plan_trip()         distance -> mode -> minutes -> cost -> effort
                       energy match        trip effort vs. the user's energy
                       importance          special events count the trip less
                       money check         ticket + travel cost vs. price slider
                   sorts the events and sends them back to the page
"""

import math


# ---------------------------------------------------------------------------
# Settings. All rough guesses: change them until the results feel right.
# ---------------------------------------------------------------------------

DETOUR = 1.3  # roads are never straight: real distance = straight line x 1.3

# For each way of getting there:
#   speed           km/h while moving
#   wait            minutes before you move (waiting for a tram, ordering a taxi, parking)
#   hassle          effort just for choosing this mode (tickets, finding the stop, ...)
#   effort_per_min  how tiring one minute of it is
MODES = {
    "walk":   {"speed": 5,  "wait": 0,  "hassle": 0.0, "effort_per_min": 0.15},
    "bike":   {"speed": 15, "wait": 2,  "hassle": 0.5, "effort_per_min": 0.12},
    "public": {"speed": 25, "wait": 10, "hassle": 1.5, "effort_per_min": 0.05},
    "car":    {"speed": 35, "wait": 10, "hassle": 2.0, "effort_per_min": 0.04},
    "taxi":   {"speed": 35, "wait": 8,  "hassle": 1.5, "effort_per_min": 0.02},
}

# When choosing a mode, CHF 5 feels about as bad as 1 point of effort.
CHF_PER_EFFORT_POINT = 5

# Used when the page doesn't send a location
BERN = {"name": "Bern HB", "lat": 46.9490, "lon": 7.4391}


# ---------------------------------------------------------------------------
# Sample events. Fiona's real data replaces this: each event needs these fields.
#   lat, lon     where it is
#   price        ticket price per person in CHF
#   importance   how special it is: 0 = happens every week, 1 = once a year
# ---------------------------------------------------------------------------

EVENTS = [
    {"name": "Pub quiz near the station",     "lat": 46.9485, "lon": 7.4415, "price": 0,  "importance": 0.1},
    {"name": "Board game cafe, Länggasse",    "lat": 46.9580, "lon": 7.4270, "price": 8,  "importance": 0.2},
    {"name": "Jazz in the old town",          "lat": 46.9478, "lon": 7.4520, "price": 25, "importance": 0.4},
    {"name": "Open-air cinema on the Gurten", "lat": 46.9190, "lon": 7.4395, "price": 18, "importance": 0.6},
    {"name": "Comedy night in Biel",          "lat": 47.1370, "lon": 7.2470, "price": 30, "importance": 0.3},
    {"name": "Lake concert in Thun",          "lat": 46.7580, "lon": 7.6280, "price": 40, "importance": 0.8},
    {"name": "Food festival in Fribourg",     "lat": 46.8030, "lon": 7.1510, "price": 15, "importance": 0.9},
]


def plan_trip(origin, modes, group_size, event):
    """
    Work out how to get from origin to one event.

    origin      {"lat": .., "lon": ..}    where the user is
    modes       ["walk", "public", ...]   ways the user is OK with
    group_size  number of people          (splits taxi / car costs)
    event       one event from the list

    Returns the best way to get there, plus every option so the page can show them:
        {"km": 3.4, "mode": "public", "minutes": 18, "cost_each": 3.0, "effort": 2.4,
         "options": [ {...walk...}, {...public...} ]}
    """

    # 1. Distance. Straight line, then x 1.3 for roads.
    #    1 degree of latitude is 111 km; 1 degree of longitude is 111 km x cos(latitude).
    dy = (event["lat"] - origin["lat"]) * 111
    dx = (event["lon"] - origin["lon"]) * 111 * math.cos(math.radians(origin["lat"]))
    straight_km = math.sqrt(dx * dx + dy * dy)
    km = straight_km * DETOUR

    # 2. Try every mode the user is OK with.
    options = []
    for mode in modes:
        if mode not in MODES:
            continue
        settings = MODES[mode]

        # 2a. Time: waiting + moving
        minutes = settings["wait"] + km / settings["speed"] * 60

        # 2b. Cost per person
        if mode == "walk" or mode == "bike":
            cost_each = 0.0
        elif mode == "public":
            # short city ticket, longer trips cost more per km
            if km <= 5:
                cost_each = 3.0
            else:
                cost_each = 3.0 + 0.30 * km
        elif mode == "taxi":
            # one taxi per 4 people, the fare is split
            cars = math.ceil(group_size / 4)
            cost_each = cars * (6.80 + 3.80 * km) / group_size
        elif mode == "car":
            # one car per 5 people: fuel + parking, split
            cars = math.ceil(group_size / 5)
            cost_each = cars * (0.20 * km + 5) / group_size

        # 2c. Trip effort on the same 0-10 scale as the energy slider
        effort = settings["hassle"] + minutes * settings["effort_per_min"]
        effort = min(effort, 10)

        options.append({
            "mode": mode,
            "minutes": round(minutes),
            "cost_each": round(cost_each, 2),
            "effort": round(effort, 1),
        })

    # 3. Pick the easiest option, counting money as effort too
    #    (a taxi is easy, but CHF 40 makes it feel less easy).
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


def rank_events(answers, events=EVENTS):
    """
    Score every event for this user and return them best first.
    answers is the JSON from getFilters() in filters.html.
    """

    # 1. Read the answers this needs
    origin = answers.get("from") or BERN
    modes = answers.get("modes") or ["walk"]          # nothing ticked -> walking only
    energy = answers.get("energy", 5)                  # 0-10 from the energy slider
    price_max = answers.get("priceMax", 200)
    group = str(answers.get("group", "any"))
    group_size = int(group) if group.isdigit() else 1

    results = []
    for event in events:

        # 2. How do we get there, and how tiring is it?
        trip = plan_trip(origin, modes, group_size, event)

        # 3. Energy match. A box up to my energy level, then halves for every
        #    point the trip is harder than that, but never reaches 0.
        if trip["effort"] <= energy:
            energy_match = 1.0
        else:
            energy_match = 2 ** -(trip["effort"] - energy)

        # 4. Importance. The more special the event, the less the energy match counts.
        #    importance 0 -> score stays as it is, importance 1 -> score becomes 1.
        trip_score = energy_match ** (1 - event["importance"])

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

        results.append({
            "name": event["name"],
            "score": round(score, 2),
            "trip_score": round(trip_score, 2),
            "money_score": round(money_score, 2),
            "total_cost": round(total_cost, 2),
            "trip": trip,
        })

    # 8. Best first
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


# Run this file on its own to test without the website:  python Fuzzy/Samuels_Fuzzy_Functions.py
if __name__ == "__main__":
    for energy in (2, 8):
        answers = {"from": BERN, "modes": ["walk", "bike", "public"], "energy": energy,
                   "priceMax": 60, "group": "1"}
        print(f"\nEnergy {energy}, from Bern HB, walk/bike/public:")
        for r in rank_events(answers):
            t = r["trip"]
            print(f"  {r['score']:.2f}  {r['name']:<31} {t['mode']:<6} {t['km']:>5} km "
                  f"{t['minutes']:>4} min  CHF {t['cost_each']:>5.2f}  effort {t['effort']}")
