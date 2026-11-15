"""
All event data: Fiona's made-up events + real Bern events (researched Nov 2026,
missing details made up). Everyone's functions read from EVENTS.

Every event has:
    name, venue
    lat, lon     where it is (Sam's trip planner)
    date         'YYYY-MM-DD'                                (date filter)
    start        start time in hours, 15-24 (20.5 = 20:30)   (Marlene's time function)
    price        CHF per person                              (Fiona's money function)
    capacity     how many people fit                         (Fiona's group function)
    min_age      age rating 0, 6, 12, 16, 18                 (Fiona's kids function)
    energy       how energetic the event is, 1-5             (Marlene's energy function)
    keywords     list of keywords the event has, picked like checkboxes (Marlene's keywords)
    repeats      'weekly', 'monthly', 'seasonal', 'once' or 'yearly' (how special it is)
    source       'made up' or where the info came from
    distance_km  filled in at the bottom: distance from Bern HB
"""

import math

# All keywords an event can have. The keyword checkboxes in filters.html use the same list.
KEYWORDS = ['party', 'dance', 'social', 'quiet', 'creative', 'outdoor', 'food', 'sport',
            'pop', 'techno', 'edm', 'made for kids', 'made for pets']


EVENTS = [

    # ======================= Fiona's events (made up) =======================

    dict(name='Board game café', venue='Länggasse', lat=46.9560, lon=7.4290,
         date='2026-11-20', start=19, price=12, capacity=40, min_age=0, energy=2, repeats='weekly',
         keywords=['social', 'quiet', 'creative', 'made for kids'], source='made up'),

    dict(name='Indie cinema', venue='Lorraine', lat=46.9565, lon=7.4440,
         date='2026-11-20', start=20, price=15, capacity=80, min_age=12, energy=1, repeats='weekly',
         keywords=['quiet', 'creative'], source='made up'),

    dict(name='Jazz in a small bar', venue='Matte', lat=46.9455, lon=7.4530,
         date='2026-11-20', start=20.5, price=25, capacity=30, min_age=16, energy=2, repeats='weekly',
         keywords=['quiet', 'social'], source='made up'),

    dict(name='Thermal spa evening', venue='Belp', lat=46.8900, lon=7.5000,
         date='2026-11-27', start=18, price=70, capacity=50, min_age=16, energy=1, repeats='weekly',
         keywords=['quiet'], source='made up'),

    dict(name='Pottery workshop', venue='Breitenrain', lat=46.9600, lon=7.4550,
         date='2026-11-20', start=18.5, price=50, capacity=8, min_age=6, energy=2, repeats='monthly',
         keywords=['creative', 'quiet', 'social'], source='made up'),

    dict(name='Comedy open mic', venue='Wankdorf', lat=46.9630, lon=7.4650,
         date='2026-11-20', start=20, price=10, capacity=60, min_age=16, energy=3, repeats='weekly',
         keywords=['social', 'creative'], source='made up'),

    dict(name='Karaoke night', venue='Bümpliz', lat=46.9450, lon=7.3900,
         date='2026-11-27', start=21, price=15, capacity=25, min_age=12, energy=4, repeats='weekly',
         keywords=['party', 'pop', 'social'], source='made up'),

    dict(name="Friend's house party", venue='Wabern', lat=46.9300, lon=7.4500,
         date='2026-11-20', start=21, price=0, capacity=15, min_age=16, energy=4, repeats='once',
         keywords=['party', 'social', 'dance', 'pop'], source='made up'),

    dict(name='Tasting menu dinner', venue='Muri bei Bern', lat=46.9310, lon=7.4870,
         date='2026-11-27', start=19, price=120, capacity=12, min_age=12, energy=2, repeats='seasonal',
         keywords=['food', 'social', 'quiet'], source='made up'),

    dict(name='Full-moon hike', venue='Bantiger', lat=46.9780, lon=7.5280,
         date='2026-11-20', start=19.5, price=0, capacity=25, min_age=6, energy=3, repeats='monthly',
         keywords=['outdoor', 'social', 'quiet', 'sport', 'made for pets'], source='made up'),

    dict(name='Lantern parade', venue='Old town', lat=46.9480, lon=7.4520,
         date='2026-11-27', start=18, price=0, capacity=500, min_age=0, energy=3, repeats='yearly',
         keywords=['outdoor', 'social', 'creative', 'made for kids'], source='made up'),

    dict(name='Techno open-air', venue='Thun lakeside', lat=46.7550, lon=7.6300,
         date='2026-11-20', start=22, price=45, capacity=2000, min_age=18, energy=5, repeats='once',
         keywords=['party', 'techno', 'edm', 'dance', 'outdoor'], source='made up'),

    dict(name='Festival headliner', venue='Interlaken', lat=46.6863, lon=7.8632,
         date='2026-11-27', start=20, price=150, capacity=10000, min_age=16, energy=5, repeats='yearly',
         keywords=['party', 'pop', 'edm', 'dance', 'outdoor', 'social'], source='made up'),

    # ======================= Real Bern events =======================
    # Dates are real; prices, start times and capacities are partly made up.

    dict(name='Zibelemärit (onion market)', venue='Old town / Bundesplatz', lat=46.9468, lon=7.4440,
         date='2026-11-23', start=16, price=0, capacity=50000, min_age=0, energy=3, repeats='yearly',
         keywords=['outdoor', 'social', 'food', 'made for kids'],
         source='https://www.myswitzerland.com/en-ch/experiences/events/onion-market-zibelemaerit/'),
         # really open 06:00-18:00; start=16 = an after-class visit

    dict(name='Rendez-vous Bundesplatz light show', venue='Bundesplatz', lat=46.9468, lon=7.4440,
         date='2026-11-20', start=19, price=0, capacity=6000, min_age=0, energy=1, repeats='yearly',
         keywords=['creative', 'outdoor', 'made for kids'],
         source='https://www.plattformj.ch/artikel/247690/'),

    dict(name='Sternenmarkt (Christmas market)', venue='Kleine Schanze', lat=46.9461, lon=7.4405,
         date='2026-11-19', start=17, price=0, capacity=3000, min_age=0, energy=2, repeats='seasonal',
         keywords=['food', 'social', 'outdoor', 'party'],
         source='https://www.bls.ch/de/freizeit-und-ferien/events/berner-weihnachtsmaerkte'),

    dict(name='Christmas market at the Münster', venue='Münsterplatz', lat=46.9474, lon=7.4515,
         date='2026-11-28', start=16, price=0, capacity=3000, min_age=0, energy=2, repeats='seasonal',
         keywords=['food', 'outdoor', 'social', 'made for kids'],
         source='https://www.bls.ch/de/freizeit-und-ferien/events/berner-weihnachtsmaerkte'),

    dict(name='Campus Festival (Uni Bern)', venue='Unitobler, Lerchenweg 36', lat=46.9545, lon=7.4290,
         date='2026-11-07', start=19, price=20, capacity=3000, min_age=18, energy=5, repeats='yearly',
         keywords=['party', 'social', 'dance', 'pop'],
         source='https://www.campusfestival.ch/'),

    dict(name='Gurtenfestival', venue='Gurten', lat=46.9190, lon=7.4395,
         date='2026-07-15', start=17, price=131, capacity=20000, min_age=0, energy=5, repeats='yearly',
         keywords=['party', 'pop', 'dance', 'outdoor', 'social', 'edm'],
         source='https://www.bls.ch/en/freizeit-und-ferien/events/gurten-festival-ag-gurtenfestival'),

    dict(name='Ice skating at Bundesplatz', venue='Bundesplatz', lat=46.9468, lon=7.4440,
         date='2026-12-12', start=18, price=10, capacity=500, min_age=0, energy=3, repeats='seasonal',
         keywords=['sport', 'outdoor', 'social', 'made for kids'],
         source='https://bern.com/en/event/kunsteisbahn-bundesplatz_243175ac-41d6-418f-9b93-ca25fbf5ff43'),

    dict(name='Raclette by the campfire, Gurten', venue='Gurten Kulm', lat=46.9190, lon=7.4395,
         date='2026-11-27', start=18, price=73, capacity=60, min_age=0, energy=3, repeats='seasonal',
         keywords=['food', 'outdoor', 'social'],
         source='https://www.gurtenpark.ch/en/events-meetings/team-events/outdoor-raclette/'),

    dict(name='Raclette in the yurt, Youth Hostel', venue='Weihergasse 4 (Marzili)', lat=46.9440, lon=7.4465,
         date='2026-11-20', start=19, price=35, capacity=20, min_age=0, energy=1, repeats='seasonal',
         keywords=['food', 'social', 'quiet'],
         source='https://www.youthhostel.ch/de/angebote/raclette-jurte-bern'),

    dict(name="Pub quiz at McCarthy's", venue='Aarbergergasse 20', lat=46.9493, lon=7.4415,
         date='2026-11-16', start=20, price=0, capacity=60, min_age=16, energy=2, repeats='weekly',
         keywords=['social', 'quiet'],
         source='https://restaurantguru.com/McCarthys-Irish-Pub-Bern-Bern'),

    dict(name='Karaoke at the Shamrock', venue='Schwarztorstrasse 11', lat=46.9455, lon=7.4370,
         date='2026-11-19', start=21, price=0, capacity=80, min_age=16, energy=4, repeats='weekly',
         keywords=['party', 'pop', 'social'],
         source='https://theshamrock.ch/'),

    dict(name='English Comedy Night at the Shamrock', venue='Schwarztorstrasse 11', lat=46.9455, lon=7.4370,
         date='2026-11-20', start=20, price=15, capacity=60, min_age=16, energy=2, repeats='monthly',
         keywords=['social', 'creative'],
         source='https://eventfrog.ch/en/events/bern/comedy-cabaret.html'),

    dict(name='Stand Up Bern Open Mic', venue='Les Amis, Rathausgasse 63', lat=46.9490, lon=7.4500,
         date='2026-12-02', start=20, price=10, capacity=50, min_age=16, energy=2, repeats='monthly',
         keywords=['social', 'creative'],
         source='https://eventfrog.ch/en/events/bern/comedy-cabaret.html'),

    dict(name='English comedy with Teddy Hall', venue='Les Amis, Rathausgasse 63', lat=46.9490, lon=7.4500,
         date='2026-11-26', start=20, price=20, capacity=80, min_age=16, energy=2, repeats='once',
         keywords=['social', 'creative'],
         source='https://eventfrog.ch/en/events/bern/comedy-cabaret.html'),

    dict(name='Baschi live', venue='Bierhübeli, Neubrückstrasse 43', lat=46.9575, lon=7.4385,
         date='2026-11-21', start=20, price=55, capacity=1000, min_age=0, energy=4, repeats='once',
         keywords=['pop', 'party', 'dance', 'social'],
         source='https://www.ticketcorner.ch/en/city/bern-14/'),

    dict(name='Charles Nguela: Timing (comedy)', venue='Bierhübeli, Neubrückstrasse 43', lat=46.9575, lon=7.4385,
         date='2026-11-24', start=20, price=45, capacity=1000, min_age=12, energy=2, repeats='once',
         keywords=['social', 'creative'],
         source='https://www.songkick.com/metro-areas/27452-switzerland-bern/genre/comedy'),

    dict(name='Nachtseminar student party', venue='Kater Karlo', lat=46.9478, lon=7.4410,
         date='2026-11-26', start=22, price=15, capacity=800, min_age=18, energy=5, repeats='monthly',
         keywords=['party', 'dance', 'social', 'edm', 'pop'],
         source='https://www.nachtseminar.ch/bern'),

    dict(name='English yoga class, Yogaalaya', venue='Schlösslistrasse 15', lat=46.9445, lon=7.4320,
         date='2026-11-18', start=18.5, price=25, capacity=20, min_age=12, energy=2, repeats='weekly',
         keywords=['sport', 'quiet'],
         source='https://www.yoga-bern.ch/en/'),

    dict(name='Jivamukti yoga (English), Hrdayam', venue='Gerechtigkeitsgasse 77', lat=46.9480, lon=7.4565,
         date='2026-11-17', start=18, price=30, capacity=20, min_age=12, energy=3, repeats='weekly',
         keywords=['sport', 'quiet'],
         source='https://www.momoyoga.com/hrdayambern/schedule'),
]


# Example of what the user answers look like (same shape as the JSON from filters.html)
SAMPLE_USER = dict(
    energy=dict(level=3, word='okay', importance=5),
    times=['evening', 'night'],
    dateFrom='2026-11-15', dateTo='2026-11-30',
    money=dict(max=40, min=0, importance=4),
    group=dict(size=6, importance=4),
    kids_ok=dict(age=10, importance=3),   # None if no kids come
    keywords=['social', 'quiet'],         # [] if no keywords are selected
    keyword_importance=5,
    modes=['walk', 'public'],
)


# distance_km from Bern HB (straight line x 1.3), for code that doesn't use lat/lon
BERN_HB = (46.9490, 7.4391)
for e in EVENTS:
    dy = (e['lat'] - BERN_HB[0]) * 111
    dx = (e['lon'] - BERN_HB[1]) * 111 * math.cos(math.radians(BERN_HB[0]))
    e['distance_km'] = round(math.sqrt(dx * dx + dy * dy) * 1.3, 1)
