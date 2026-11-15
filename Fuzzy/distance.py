

INF = float("inf")

# Each word is a fuzzy set over km: trapezoid (a, b, c, d).
# Rises from a to b, fully true from b to c, falls from c to d.
# Keep these the same as DIST_WORDS in event-search/filters.html.
WORDS = {
    "walk":    (0, 0, 2, 5),
    "bike":    (2, 5, 12, 25),
    "commute": (12, 25, 45, 70),
    "travel":  (45, 70, INF, INF),
}

# How many km past your limit you would still go, depending on how you get there.
# One extra km on foot hurts. Ten extra km on a train hardly matters.
EXTRA_KM = {"walk": 1, "bike": 4, "commute": 10, "travel": 40}


def trapezoid(x, a, b, c, d):
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (d - x) / (d - c)


def word_memberships(km):
    """How true each word is for a distance, e.g. 3.5 km -> walk 0.5, bike 0.5."""
    return {w: trapezoid(km, *shape) for w, shape in WORDS.items()}


def best_word(km):
    m = word_memberships(km)
    return max(m, key=m.get)


def distance_function(slider_km, word, event_km):
    """
    How well an event event_km away fits the distance the user picked.
    1.0 up to slider_km, then fades to 0 over EXTRA_KM[word] more km.
    """
    if word not in EXTRA_KM:
        word = best_word(slider_km)
    if event_km <= slider_km:
        return 1.0
    return max(0.0, 1 - (event_km - slider_km) / EXTRA_KM[word])


if __name__ == "__main__":
    print("Which words fit a distance:")
    for km in (1, 3.5, 9, 20, 50, 80):
        m = {w: round(v, 2) for w, v in word_memberships(km).items() if v > 0}
        print(f"  {km:>5} km  {m}")

    print("\nUser picked 9 km by bike. How well do events fit?")
    for ev in (2, 9, 10, 11, 13, 20):
        print(f"  event {ev:>3} km away -> {distance_function(9, 'bike', ev):.2f}")
