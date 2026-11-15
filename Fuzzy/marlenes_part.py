"""
Marlene's part: energy, time and keyword membership functions.
Taken from notebooks/Marlene_working.ipynb, without the plots.

The notebook used scikit-fuzzy for the gaussian curves. Here the same maths is written
with plain numpy (gaussmf -> np.exp, interp_membership -> np.interp), so the app only
needs numpy. The results are the same.

    energy_membership('good', 7, 5)        -> 0.422
    time_membership(17.0)                  -> {'early evening': 1.0, 'evening': 0.33, 'night': 0.0}
    keyword_membership(alpha=1, beta=0.5)  -> 0.5     (0-1: 0 if the event doesn't have it)
"""

from datetime import datetime

import numpy as np


# ---------------------------------------------------------------------------
# Energy
# Users pick one of five energy levels. Events have a recommended energy level 1-5.
# Each level is a gaussian curve; the importance (0-10) sets how steep the curves are.
# ---------------------------------------------------------------------------

ENERGY_UNIVERSE = np.linspace(1, 5, 401)    # energy is a scale of 1 to 5

CENTERS = {'drained': 1, 'tired': 2, 'okay': 3, 'good': 4, 'buzzing': 5}


def sigma_for_importance(imp):
    # slopes: 0 -> flat, 1->~1.09, 5->~0.87, 7->~0.76, 9->~0.65, 10->0.30 (no overlap)
    if imp <= 0:
        return None
    if imp >= 10:
        return 0.30
    if imp >= 9:
        return 0.65 - 0.35 * (imp - 9)
    return 1.15 - 0.0556 * imp


def energy_curve(user_energy, importance):
    """The fuzzy set for one energy word ('drained' ... 'buzzing') at this importance."""
    s = sigma_for_importance(importance)
    if s is None:
        # flat line at 1.0 -> 1 for any level (no effect on event order)
        return np.ones_like(ENERGY_UNIVERSE)
    # edges are a little wider so the peaks are centered right
    sigma = s * 1.25 if user_energy in ('drained', 'buzzing') else s
    c = CENTERS[user_energy]
    return np.exp(-((ENERGY_UNIVERSE - c) ** 2) / (2 * sigma ** 2))


def energy_membership(user_energy, importance, event_energy):
    """How well an event's energy (1-5) fits the user's energy word.

    user_energy   'drained', 'tired', 'okay', 'good' or 'buzzing'
    importance    0-10 from the importance slider
    event_energy  the event's recommended energy level, 1-5
    """
    curve = energy_curve(user_energy, importance)
    event_mu = np.interp(event_energy, ENERGY_UNIVERSE, curve)
    return round(float(event_mu), 3)


getImportance = energy_membership   # the name used in the notebook


# ---------------------------------------------------------------------------
# Time
# early evening / evening / night as overlapping trapezoids, so every time has a
# label that is 100% relevant. In the UI it's a checklist where users can pick several.
# ---------------------------------------------------------------------------

T = np.linspace(15, 24, 901)  # events can start between 15:00 and 24:00


def trap(a, b, c, d, x=T):
    """Trapezoid: rises a->b, flat b->c, falls c->d (a<=b<=c<=d)."""
    up = (x >= a).astype(float) if b == a else (x - a) / (b - a)
    down = (x <= d).astype(float) if d == c else (d - x) / (d - c)
    return np.clip(np.minimum(up, down), 0, 1)


# 15-24 is 9 hours, 3 hours each: 15-18h early evening, 18-21 evening, 21-24 night
TIME_SETS = {
    'early evening': trap(15, 15, 18, 19.5),
    'evening':       trap(16.5, 18, 21, 22.5),
    'night':         trap(19.5, 21, 24, 24),
}


def time_membership(hour):
    """Return {label: membership} for a crisp clock time."""
    idx = int(np.argmin(np.abs(T - hour)))
    return {k: float(v[idx]) for k, v in TIME_SETS.items()}


# ---------------------------------------------------------------------------
# Keywords
# For a keyword the user selected:
#   alpha = 1 if the event has it, 0 if not
#   beta  = the user's importance, 0 (trivial) to 1 (mandatory)
# m goes from 0 to 1:
#   alpha = 1, beta = 0.5 -> m = 0.5
#   alpha = 1, beta = 1   -> m = 1
#   alpha = 1, beta = 0   -> m = 0
#   alpha = 0             -> m = 0
# ---------------------------------------------------------------------------

def keyword_membership(alpha, beta):
    """Return keyword relevance m in [0, 1]. Only call this for keywords the user selected.
    alpha = 1 if event has keyword, 0 otherwise.
    beta = user importance 0 (trivial) to 1 (mandatory).
    """
    if alpha == 1:
        return beta  # == beta for beta in [0,1]
    else:
        return 0


def keyword_fit(alpha, beta):
    """The first version, m in [-1, 1], made for adding up the keywords.
    -1 = wanted it a lot, event doesn't have it, 1 = wanted it a lot, event has it.
    """
    if alpha == 1:
        return alpha - abs(1 - beta)  # == beta
    else:
        return alpha - beta  # == -beta


# ---------------------------------------------------------------------------
# Date
# ---------------------------------------------------------------------------

# quick function to check if an event occurs within the selected date range
def date_passes(event_date, start_date, end_date):
    if not start_date or not end_date:  # no dates selected = show all
        return True

    event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    return start_date <= event_date <= end_date


# Run this file on its own to check it matches the notebook:  python Fuzzy/marlenes_part.py
if __name__ == "__main__":
    print("energy 'good', importance 7, event 5 ->", energy_membership('good', 7, 5), "(notebook: 0.422)")
    print("17:00 ->", time_membership(17.0))
    print("keyword alpha=1 beta=0.5 ->", keyword_membership(1, 0.5), "(notebook: 0.5)")
    print("keyword alpha=0 beta=0.8 ->", keyword_membership(0, 0.8), "(notebook: 0)")
    print("date 2026-11-15 in 14-17 Nov ->", date_passes("2026-11-15", "2026-11-14", "2026-11-17"), "(notebook: True)")
