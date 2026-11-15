"""
Sample data (made up, not real events). From Fiona's notebook.

Each event has:
    price        CHF per person
    capacity     how many people fit
    min_age      age rating (0, 6, 12, 16, 18)
    energy       how energetic the event is, 1-5
    distance_km  distance (Sam's trip planner will replace this with lat, lon)
    start        start time in hours (20.5 = 20:30)
    date         'YYYY-MM-DD'
    keywords     how well the event fits each keyword, 0-1
"""

EVENTS = [
    dict(name='Board game café',      price=12,  capacity=40,    min_age=0,  energy=2, distance_km=1,  start=19,   date='2026-11-20',
         keywords=dict(social=1.0, quiet=0.6, creative=0.3)),
    dict(name='Indie cinema',         price=15,  capacity=80,    min_age=12, energy=1, distance_km=1,  start=20,   date='2026-11-20',
         keywords=dict(quiet=1.0, creative=0.4)),
    dict(name='Jazz in a small bar',  price=25,  capacity=30,    min_age=16, energy=2, distance_km=3,  start=20.5, date='2026-11-20',
         keywords=dict(quiet=0.6, social=0.6, creative=0.3)),
    dict(name='Thermal spa evening',  price=70,  capacity=50,    min_age=16, energy=1, distance_km=12, start=18,   date='2026-11-27',
         keywords=dict(quiet=1.0)),
    dict(name='Pottery workshop',     price=50,  capacity=8,     min_age=6,  energy=2, distance_km=2,  start=18.5, date='2026-11-20',
         keywords=dict(creative=1.0, quiet=0.7, social=0.5)),
    dict(name='Comedy open mic',      price=10,  capacity=60,    min_age=16, energy=3, distance_km=4,  start=20,   date='2026-11-20',
         keywords=dict(social=0.8, creative=0.5)),
    dict(name='Karaoke night',        price=15,  capacity=25,    min_age=12, energy=4, distance_km=2,  start=21,   date='2026-11-27',
         keywords=dict(party=0.8, pop=1.0, social=1.0, dance=0.3)),
    dict(name="Friend's house party", price=0,   capacity=15,    min_age=16, energy=4, distance_km=3,  start=21,   date='2026-11-20',
         keywords=dict(party=1.0, social=1.0, dance=0.7, pop=0.6)),
    dict(name='Tasting menu dinner',  price=120, capacity=12,    min_age=12, energy=2, distance_km=5,  start=19,   date='2026-11-27',
         keywords=dict(social=0.7, quiet=0.7)),
    dict(name='Full-moon hike',       price=0,   capacity=25,    min_age=6,  energy=3, distance_km=15, start=19.5, date='2026-11-20',
         keywords=dict(outdoors=1.0, social=0.6, quiet=0.7)),
    dict(name='Lantern parade',       price=0,   capacity=500,   min_age=0,  energy=3, distance_km=1,  start=18,   date='2026-11-27',
         keywords=dict(outdoors=1.0, social=0.8, creative=0.5)),
    dict(name='Techno open-air',      price=45,  capacity=2000,  min_age=18, energy=5, distance_km=25, start=22,   date='2026-11-20',
         keywords=dict(party=1.0, techno=1.0, edm=1.0, dance=1.0, outdoors=0.8)),
    dict(name='Festival headliner',   price=150, capacity=10000, min_age=16, energy=5, distance_km=60, start=20,   date='2026-11-27',
         keywords=dict(party=0.9, pop=0.8, edm=0.5, dance=0.8, outdoors=1.0, social=0.8)),
]


# Example of what the user answers look like for Fiona's functions
SAMPLE_USER = dict(
    money=dict(max=40, min=0, importance=4),
    group=dict(size=6, importance=4),
    kids_ok=dict(age=10, importance=3),   # None if no kids come
    keywords=['social', 'quiet'],         # [] if no keywords are selected
)
