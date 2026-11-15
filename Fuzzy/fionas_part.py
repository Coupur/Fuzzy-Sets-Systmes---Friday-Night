"""
Fiona's part: money, group size and "can kids come" membership functions, the relevance score 
The data is in event_data.py.

    rank(user)  ->  list of events, best first, each with its scores
"""

import numpy as np

try:
    # when app.py uses this file
    from Fuzzy.marlenes_part import energy_membership, time_membership, keyword_membership
    from Fuzzy.event_data import EVENTS, SAMPLE_USER
except ImportError:
    # when this file is run on its own
    from marlenes_part import energy_membership, time_membership, keyword_membership
    from event_data import EVENTS, SAMPLE_USER


def shape(a, b, c, d, x):
    """Trapezoid fuzzy set: rises from a to b, stays at 1 until c, falls to d."""
    up = (x >= a).astype(float) if b == a else (x - a) / (b - a)
    down = (x <= d).astype(float) if d == c else (d - x) / (d - c)
    return np.clip(np.minimum(up, down), 0, 1)


# ---------------------------------------------------------------------------
# Money range membership function
# ---------------------------------------------------------------------------

MONEY = np.linspace(0, 300, 1501)

MONEY_SOFTNESS = 1.0 # wideness of slopes at importance 0 (1 = as wide as the range)


def money_membership(max_money, importance, min_money=0, x=MONEY):
    """Fuzzy set for 'how much I want to spend', on the grid x (in CHF).

    max_money   upper end of the range
    min_money   lower end of the range (default 0)
    importance  0-10: 10 = crisp rectangle, 0 = very soft slopes
    """
    importance = float(np.clip(importance, 0, 10))
    softness = (10 - importance) / 10 # 0 = crisp, ..., 1 = very soft slope
    w = softness * MONEY_SOFTNESS * (max_money - min_money)

    a = max(min_money - w, 0)
    b = min_money
    c = max_money
    d = max_money + w
    return shape(a, b, c, d, x)


# ---------------------------------------------------------------------------
# Group size membership function
# ---------------------------------------------------------------------------

PEOPLE = np.linspace(0, 20, 1001)

GROUP_SOFTNESS = 1.0 

def group_membership(size, importance, x=PEOPLE):
    """Fuzzy set for 'a group of at least this size', on the grid x (in people).

    size        the group size (number of people)
    importance  0-10: 10 = crisp step (rectangle), 0 = very soft ramp
    """
    importance = float(np.clip(importance, 0, 10))
    softness = (10 - importance) / 10
    w = softness * GROUP_SOFTNESS * size

    a = max(size - w, 0) # the slope starts here (not below 0)
    b = size
    top = x.max()
    return shape(a, b, top, top, x)


# ---------------------------------------------------------------------------
# "Can kids come?" membership function
# (not the same as the fuzzy keyword "Is it for kids?")
# ---------------------------------------------------------------------------

AGE = np.linspace(0, 18, 1801)
KIDS_OK_SOFTNESS = 1.0

def kids_ok_membership(min_age, importance, x=AGE):
    """Fuzzy set 'this age is OK to attend the event'.

    min_age     minimum age of the event (like a film rating: 0, 6, 12, 16, 18)
    importance  0-10: 10 = crisp step (rectangle), 0 = very soft ramp
    x           the age of the child
    """
    importance = float(np.clip(importance, 0, 10))
    softness = (10 - importance) / 10
    w = softness * KIDS_OK_SOFTNESS * min_age

    a = max(min_age - w, 0)
    top = x.max()
    return shape(a, min_age, top, top, x)


# ---------------------------------------------------------------------------
# Score of one event for each criterion
# ---------------------------------------------------------------------------

def at(x):
    return np.array([float(x)]) # a we read the curve at that point


def score_money(event, u):
    if u.get('money') is None:
        return None
    m = u['money']
    return float(money_membership(m['max'], m['importance'], m['min'], x=at(event['price']))[0])


def score_group(event, u):
    if u.get('group') is None:
        return None
    g = u['group']
    return float(group_membership(g['size'], g['importance'], x=at(event['capacity']))[0])


def score_kids_ok(event, u):
    if u.get('kids_ok') is None: # no kids come -> this criterion is left out
        return None
    k = u['kids_ok']
    return float(kids_ok_membership(event['min_age'], k['importance'], x=at(k['age']))[0])

def score_energy(event, u):
    if u.get('energy') is None:
        return None
    e = u['energy']
    return energy_membership(e['word'], e['importance'], event['energy'])


def score_time(event, u):
    if not u.get('times'): # no time selected -> this criterion is left out
        return None
    mu = time_membership(event['start'])
    # the user can tick several times: the event fits if it fits ONE of them (generous OR)
    return generous_or([mu[t] for t in u['times']])


def score_date(event, u):
    """Crisp filter: 1 if the event is inside the date range, else 0."""
    d_from, d_to = u.get('dateFrom'), u.get('dateTo')
    if not d_from and not d_to: # no dates entered -> no filter
        return None
    if d_from and event['date'] < d_from: # 'YYYY-MM-DD'
        return 0.0
    if d_to and event['date'] > d_to:
        return 0.0
    return 1.0


def score_distance(event, u):
    # TODO Sam's travel / distance function goes here. For now the criterion is left out.
    return None


# Combining the fitting of membership functions and keywords separately
def strict_and(mu):
    """Product: every score has to be good, one 0 makes the result 0."""
    return float(np.prod(np.asarray(mu, float)))


def generous_or(mu):
    """1 - product of (1 - score): high as soon as one score is high."""
    return float(1 - np.prod(1 - np.asarray(mu, float)))


# Keywords: generous OR. This is high as soon as one keyword of the event matches the user's needs
def keyword_degree(event, keyword, importance):
    """How well the event fits one keyword the user selected, as a score from 0 to 1.

    Uses Marlene's keyword_membership (m from -1 to 1) and moves it to 0..1,
    because strict_and and generous_or need scores between 0 and 1:
        0   = the user wanted it a lot, the event doesn't have it
        0.5 = the user doesn't care about this keyword
        1   = the user wanted it a lot, the event has it
    importance  the keyword importance slider, 0-10
    """
    alpha = 1 if keyword in event['keywords'] else 0
    beta = float(np.clip(importance / 10, 0, 1))      # slider 0-10 -> 0-1
    m = keyword_membership(alpha, beta)
    return (m + 1) / 2


def score_keywords(event, u):
    if not u.get('keywords'): # no keywords selected -> this criterion is left out
        return None
    imp = u.get('keyword_importance', 5)
    return generous_or([keyword_degree(event, k, imp) for k in u['keywords']])


# Strict-AND criteria. Every criterion has to be good. If one score is 0, the result is 0
# (the date is not in here: it is a filter in rank())
SCORERS = {
    'money': score_money,
    'group size': score_group,
    'kids_ok': score_kids_ok,
    'energy': score_energy,
    'time': score_time,
    'distance': score_distance,
    'keywords': score_keywords, # already combined with OR inside
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

    Events outside the chosen dates are not shown at all (crisp date filter).
    Returns a plain list of dicts (not a pandas table).
    In a notebook you can still get a table with: pd.DataFrame(rank(user))
    """
    rows = []
    for e in events:
        if score_date(e, u) == 0: # other dates are filtered out, they don't get a rank
            continue
        total, scores = relevance(e, u)
        rows.append(dict(event=e['name'], relevance=total, **scores))
    rows.sort(key=lambda r: r['relevance'], reverse=True)
    return rows


# Run this file on its own to test it:  python Fuzzy/fionas_part.py
if __name__ == "__main__":
    for r in rank(SAMPLE_USER):
        scores = "  ".join(f"{k} {v:.2f}" for k, v in r.items() if k not in ('event', 'relevance'))
        print(f"{r['relevance']:.2f}  {r['event']:<22} {scores}")
