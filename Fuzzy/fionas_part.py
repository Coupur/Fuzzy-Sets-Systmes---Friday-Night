"""
Fiona's part: money, group size and "can kids come" membership functions,
plus the relevance score that combines them. Taken from fionas_part.ipynb,
without the plots. The data lives in event_data.py.

    rank(user)  ->  list of events, best first, each with its scores
"""

import numpy as np

try:
    from Fuzzy.event_data import EVENTS, SAMPLE_USER   # when app.py uses this file
except ImportError:
    from event_data import EVENTS, SAMPLE_USER          # when this file is run on its own


def shape(a, b, c, d, x):
    """Trapezoid fuzzy set: rises from a to b, stays at 1 until c, falls to d."""
    up = (x >= a).astype(float) if b == a else (x - a) / (b - a)
    down = (x <= d).astype(float) if d == c else (d - x) / (d - c)
    return np.clip(np.minimum(up, down), 0, 1)


# ---------------------------------------------------------------------------
# Money range membership function
# ---------------------------------------------------------------------------

MONEY = np.linspace(0, 300, 1501)    # money axis in CHF

MONEY_SOFTNESS = 1.0   # how wide the slopes get at importance 0 (1.0 = as wide as the range)


def money_membership(max_money, importance, min_money=0, x=MONEY):
    """Fuzzy set for 'how much I want to spend', on the grid x (in CHF).

    max_money   upper end of the range
    min_money   lower end of the range (default 0)
    importance  0-10: 10 = crisp rectangle, 0 = very soft slopes
    """
    importance = float(np.clip(importance, 0, 10))
    softness = (10 - importance) / 10                         # 0 = crisp, ..., 1 = very soft slope
    w = softness * MONEY_SOFTNESS * (max_money - min_money)   # width of each slope

    a = max(min_money - w, 0)
    b = min_money
    c = max_money
    d = max_money + w
    return shape(a, b, c, d, x)


# ---------------------------------------------------------------------------
# Group size membership function
# ---------------------------------------------------------------------------

PEOPLE = np.linspace(0, 20, 1001)    # group size axis in people

GROUP_SOFTNESS = 1.0   # how far left the ramp starts at importance 0 (1.0 = starts at 0)


def group_membership(size, importance, x=PEOPLE):
    """Fuzzy set for 'a group of at least this size', on the grid x (in people).

    size        the group size (number of people)
    importance  0-10: 10 = crisp step (rectangle), 0 = very soft ramp
    """
    importance = float(np.clip(importance, 0, 10))
    softness = (10 - importance) / 10          # 0 = crisp, ..., 1 = very soft ramp
    w = softness * GROUP_SOFTNESS * size       # width of the rising side

    a = max(size - w, 0)    # the ramp starts here (not below 0)
    b = size                # from here on the membership is 1
    top = x.max()           # c = d = end of the axis, so it stays at 1 forever
    return shape(a, b, top, top, x)


# ---------------------------------------------------------------------------
# "Can kids come?" membership function
# (not the same as the fuzzy keyword "Is it for kids?")
# ---------------------------------------------------------------------------

AGE = np.linspace(0, 18, 1801)   # age of the child who wants to attend
KIDS_OK_SOFTNESS = 1.0           # how far left the ramp starts at importance 0 (1.0 = starts at age 0)


def kids_ok_membership(min_age, importance, x=AGE):
    """Fuzzy set 'this age is OK to attend the event'.

    min_age     minimum age of the event (like a film rating: 0, 6, 12, 16, 18)
    importance  0-10: 10 = crisp step (rectangle), 0 = very soft ramp
    x           the age of the child
    """
    importance = float(np.clip(importance, 0, 10))
    softness = (10 - importance) / 10             # 0 = crisp, ..., 1 = very soft ramp
    w = softness * KIDS_OK_SOFTNESS * min_age     # width of the rising side

    a = max(min_age - w, 0)    # the ramp starts here (not below 0)
    top = x.max()              # stays at 1 until the end of the axis
    return shape(a, min_age, top, top, x)


# ---------------------------------------------------------------------------
# Score of one event for each criterion
# ---------------------------------------------------------------------------

def at(x):
    return np.array([float(x)])   # a single value as a grid, so we read the curve at that point


def score_money(event, u):
    if u.get('money') is None:
        return None
    m = u['money']
    return float(money_membership(m['max'], m['importance'], m['min'], x=at(event['price']))[0])


def score_group(event, u):
    if u.get('group') is None:
        return None
    g = u['group']
    # the curve belongs to the user's group size, we read it at the event's capacity
    return float(group_membership(g['size'], g['importance'], x=at(event['capacity']))[0])


def score_kids_ok(event, u):
    if u.get('kids_ok') is None:   # no kids come -> this criterion is left out
        return None
    k = u['kids_ok']
    return float(kids_ok_membership(event['min_age'], k['importance'], x=at(k['age']))[0])


# Combining the fitting of membership functions and keywords separately
def strict_and(mu):
    """Product: every score has to be good, one 0 makes the result 0."""
    return float(np.prod(np.asarray(mu, float)))


def generous_or(mu):
    """1 - product of (1 - score): high as soon as one score is high."""
    return float(1 - np.prod(1 - np.asarray(mu, float)))


# Keywords: generous OR. This is high as soon as one keyword of the event matches the user's needs
def keyword_degree(event, keyword):
    """How well the event matches one keyword (0-1).

    TODO For now it takes just an artificial value from the table. Replace this by the keyword
    membership functions once they are ready.
    """
    return event['keywords'].get(keyword, 0.0)


def score_keywords(event, u):
    if not u.get('keywords'):
        return None
    return generous_or([keyword_degree(event, k) for k in u['keywords']])


# Strict-AND criteria. Every criterion has to be good. If one score is 0, the result is 0
SCORERS = {
    'money': score_money,
    'group size': score_group,
    'kids_ok': score_kids_ok,
    'keywords': score_keywords,   # already combined with OR inside
}


# ---------------------------------------------------------------------------
# Relevance of the events
# ---------------------------------------------------------------------------

def relevance(event, u):
    """Relevance of one event for the user's wishes."""
    scores = {name: f(event, u) for name, f in SCORERS.items()}
    scores = {k: v for k, v in scores.items() if v is not None}
    return strict_and(list(scores.values())), scores


def rank(u, events=EVENTS):
    """All events with their relevance, best first.

    Returns a plain list of dicts (not a pandas table) so app.py can send it to the website.
    In a notebook you can still get a table with: pd.DataFrame(rank(user))
    """
    rows = []
    for e in events:
        total, scores = relevance(e, u)
        rows.append(dict(event=e['name'], relevance=total, **scores))
    rows.sort(key=lambda r: r['relevance'], reverse=True)
    return rows


# Run this file on its own to test it:  python Fuzzy/fionas_part.py
if __name__ == "__main__":
    for r in rank(SAMPLE_USER):
        scores = "  ".join(f"{k} {v:.2f}" for k, v in r.items() if k not in ('event', 'relevance'))
        print(f"{r['relevance']:.2f}  {r['event']:<22} {scores}")
