/* Shared fuzzy model for the input page (index.html) and the results page (results.html). */

// ============================================================
//  Fuzzy primitives
// ============================================================
const clamp01 = v => Math.max(0, Math.min(1, v));
// Trapezoid with core [b, c] and support [a, d]
function trap(x, a, b, c, d) {
  if (x < a || x > d) return 0;
  if (x >= b && x <= c) return 1;
  if (x < b) return b === a ? 1 : (x - a) / (b - a);
  return d === c ? 1 : (d - x) / (d - c);
}
// Fully true up to `ideal`, fades to 0 at `max`
function shoulder(x, ideal, max) {
  if (x <= ideal) return 1;
  if (x >= max) return 0;
  return (max - x) / (max - ideal);
}
// 0 below `a`, rises to 1 at `b`
const rise = (x, a, b) => x <= a ? 0 : x >= b ? 1 : (x - a) / (b - a);
// Zadeh's linguistic hedges: concentration and dilation
const HEDGES = {
  very:     { label: 'very',     fn: m => m * m },
  somewhat: { label: 'somewhat', fn: m => Math.sqrt(m) },
};
function centroid(f, a, b) {
  let s = 0, w = 0;
  for (let i = 0; i <= 200; i++) { const x = a + (b - a) * i / 200, m = f(x); s += x * m; w += m; }
  return w ? s / w : (a + b) / 2;
}
function lev(a, b) {
  const m = a.length, n = b.length;
  const d = Array.from({ length: m + 1 }, (_, i) => [i, ...Array(n).fill(0)]);
  for (let j = 1; j <= n; j++) d[0][j] = j;
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return d[m][n];
}
const strSim = (a, b) => a === b ? 1 : 1 - lev(a, b) / Math.max(a.length, b.length);

// ============================================================
//  Calendar: how people talk about days
// ============================================================
const TODAY = new Date(); TODAY.setHours(0, 0, 0, 0);
const dateOf = off => new Date(TODAY.getFullYear(), TODAY.getMonth(), TODAY.getDate() + off);
const offOf = d => Math.round((new Date(d).setHours(0, 0, 0, 0) - TODAY) / 864e5);
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const parseISO = s => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };

const DOW = TODAY.getDay();
const THIS_SAT = DOW === 0 ? -1 : 6 - DOW;
const NEXT_SAT = THIS_SAT + 7;
const END_OF_MONTH = offOf(new Date(TODAY.getFullYear(), TODAY.getMonth() + 1, 0));
function nextOccurrence(month, day) {
  const off = offOf(new Date(TODAY.getFullYear(), month - 1, day));
  return off >= 0 ? off : offOf(new Date(TODAY.getFullYear() + 1, month - 1, day));
}
function firstSaturdayOfDecember() {
  for (let y = TODAY.getFullYear(); ; y++) {
    const d = new Date(y, 11, 1);
    d.setDate(1 + (6 - d.getDay() + 7) % 7);
    if (offOf(d) >= 0) return offOf(d);
  }
}
const HALLOWEEN = nextOccurrence(10, 31);
const ST_NICOLAS = firstSaturdayOfDecember();

const fmtDay = off => dateOf(off).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
const fmtShort = off => dateOf(off).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
const fmtWeekday = off => dateOf(off).toLocaleDateString('en-GB', { weekday: 'long' });
const fmtHour = h => `${Math.floor(h) % 24}:${String(Math.round((h % 1) * 60)).padStart(2, '0')}`;
// "this Saturday", "next Friday", "in 5 weeks": the way people refer to dates
function relDay(off) {
  if (off < 0) return 'already passed';
  if (off === 0) return 'today';
  if (off === 1) return 'tomorrow';
  if (off <= THIS_SAT + 1) return 'this ' + fmtWeekday(off);
  if (off <= THIS_SAT + 8) return 'next ' + fmtWeekday(off);
  return `in ${Math.round(off / 7)} weeks`;
}

function km(a, b) {
  const R = 6371, rad = Math.PI / 180;
  const dLat = (b.lat - a.lat) * rad, dLng = (b.lng - a.lng) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
const scoreColor = s => `hsl(${8 + 140 * s} 62% ${46 - 6 * s}%)`;

// ============================================================
//  Demo data (Fribourg region)
// ============================================================
const CITIES = {
  fribourg: { label: 'Fribourg', lat: 46.8065, lng: 7.1620 },
  bern:     { label: 'Bern',     lat: 46.9480, lng: 7.4474 },
  murten:   { label: 'Murten',   lat: 46.9281, lng: 7.1170 },
  bulle:    { label: 'Bulle',    lat: 46.6193, lng: 7.0566 },
};

// Big moments people plan around. `loud`: how draining it is to attend.
const ANCHORS = [
  { key: 'halloween',   name: 'Halloween',                 day: HALLOWEEN, loud: .9,
    blurb: 'Costume parties, ghost walks and pumpkin carving all weekend.', going: 'Going to a Halloween party' },
  { key: 'autumnbeats', name: 'Autumn Beats festival',     day: NEXT_SAT,  loud: 1,
    blurb: 'The big indie and electronic weekender at Fri-Son.',           going: 'I have a ticket' },
  { key: 'stnicolas',   name: 'Saint-Nicolas in Fribourg', day: ST_NICOLAS, loud: .4,
    blurb: "Fribourg's biggest night of the year: the parade, the donkey and the speech from the cathedral.", going: 'Already planning to go' },
].filter(a => a.day <= 60);

// day: offset from today · buzz: how exceptional the event is · loud: how loud and draining it is
const EVENTS = [
  { id: 1,  name: 'Jazz night at Fri-Son',         place: 'Fribourg',   lat: 46.7985, lng: 7.1480, day: 2,            hour: 20.5, price: 35, energy: 4, loud: .5, buzz: .7, kid: .2, pet: 0,  group: [1, 1, 6, 10],    tags: { music: 1, jazz: 1, nightlife: .6, indoor: 1 } },
  { id: 2,  name: 'Lakeside sunset yoga',          place: 'Murten',     lat: 46.9281, lng: 7.1170, day: THIS_SAT - 1, hour: 17,   price: 20, energy: 3, loud: 0,  buzz: .5, kid: .4, pet: .3, group: [1, 1, 8, 15],    tags: { yoga: 1, outdoor: 1, wellness: .9, nature: .6 } },
  { id: 3,  name: 'Cheese and chocolate tour',     place: 'Gruyères',   lat: 46.5840, lng: 7.0820, day: THIS_SAT + 1, hour: 10,   price: 65, energy: 2, loud: .1, buzz: .6, kid: .8, pet: .2, group: [1, 2, 10, 20],   tags: { food: 1, tour: 1, culture: .6 } },
  { id: 4,  name: 'Via ferrata at Schwarzsee',     place: 'Schwarzsee', lat: 46.6680, lng: 7.2840, day: THIS_SAT,     hour: 9,    price: 90, energy: 9, loud: .1, buzz: .7, kid: .1, pet: 0,  group: [1, 2, 6, 8],     tags: { adventure: 1, outdoor: 1, nature: .8, hiking: .7, sport: .7 } },
  { id: 5,  name: 'Family science day',            place: 'Fribourg',   lat: 46.8030, lng: 7.1530, day: THIS_SAT + 1, hour: 11,   price: 0,  energy: 4, loud: .3, buzz: .5, kid: 1,  pet: 0,  group: [1, 2, 12, 30],   tags: { science: 1, museum: 1, family: 1, culture: .6, indoor: 1 } },
  { id: 6,  name: 'Old-town food walk',            place: 'Bern',       lat: 46.9480, lng: 7.4474, day: THIS_SAT,     hour: 12,   price: 55, energy: 3, loud: .2, buzz: .6, kid: .6, pet: .7, group: [1, 2, 8, 12],    tags: { food: 1, tour: .9, culture: .7, outdoor: .5 } },
  { id: 7,  name: 'Techno open-air on the Gurten', place: 'Bern',       lat: 46.9190, lng: 7.4430, day: THIS_SAT - 1, hour: 22,   price: 45, energy: 9, loud: 1,  buzz: .75, kid: 0, pet: .1, group: [1, 3, 40, 200],  tags: { music: 1, techno: 1, party: 1, nightlife: 1, outdoor: .7, festival: .5 } },
  { id: 8,  name: 'Board game café evening',       place: 'Fribourg',   lat: 46.8050, lng: 7.1600, day: 1,            hour: 19,   price: 10, energy: 1, loud: .1, buzz: .4, kid: .7, pet: .5, group: [1, 2, 6, 8],     tags: { games: 1, social: .9, indoor: 1 } },
  { id: 9,  name: 'Dog-friendly hike up Moléson',  place: 'Moléson',    lat: 46.5480, lng: 7.0180, day: THIS_SAT + 1, hour: 9.5,  price: 0,  energy: 7, loud: 0,  buzz: .6, kid: .5, pet: 1,  group: [1, 2, 10, 15],   tags: { hiking: 1, outdoor: 1, nature: 1, sport: .5 } },
  { id: 10, name: 'Organ concert in the cathedral', place: 'Fribourg',  lat: 46.8063, lng: 7.1630, day: NEXT_SAT - 2, hour: 19.5, price: 40, energy: 2, loud: .3, buzz: .6, kid: .3, pet: 0,  group: [1, 1, 6, 20],    tags: { music: 1, classical: 1, culture: .8, indoor: 1 } },
  { id: 11, name: 'Spa evening at the thermal baths', place: 'Charmey', lat: 46.6190, lng: 7.1650, day: THIS_SAT + 1, hour: 17,   price: 45, energy: 1, loud: 0,  buzz: .6, kid: .4, pet: 0,  group: [1, 1, 4, 8],     tags: { wellness: 1, water: .7, indoor: .6 } },
  { id: 12, name: 'Lantern walk through Murten',   place: 'Murten',     lat: 46.9285, lng: 7.1180, day: NEXT_SAT + 1, hour: 18,   price: 0,  energy: 3, loud: .1, buzz: .5, kid: .9, pet: .7, group: [1, 2, 20, 50],   tags: { art: .6, culture: .8, outdoor: .8, tour: .5 } },
  { id: 13, name: 'Intro to bouldering',           place: 'Thun',       lat: 46.7580, lng: 7.6280, day: 3,            hour: 16,   price: 38, energy: 8, loud: .3, buzz: .5, kid: .5, pet: 0,  group: [1, 1, 4, 6],     tags: { climbing: 1, sport: 1, indoor: 1, adventure: .6 } },
  { id: 14, name: 'Lavaux wine tasting',           place: 'Lausanne',   lat: 46.4920, lng: 6.7350, day: THIS_SAT,     hour: 15,   price: 70, energy: 2, loud: .1, buzz: .7, kid: 0,  pet: .2, group: [2, 2, 8, 12],    tags: { wine: 1, food: .7, culture: .5, outdoor: .4 } },
  { id: 15, name: 'Comedy open mic',               place: 'Bern',       lat: 46.9470, lng: 7.4390, day: 2,            hour: 20,   price: 15, energy: 3, loud: .4, buzz: .4, kid: .1, pet: 0,  group: [1, 1, 6, 10],    tags: { comedy: 1, nightlife: .6, social: .6, indoor: 1 } },
  { id: 16, name: 'Saturday market and brunch',    place: 'Fribourg',   lat: 46.8020, lng: 7.1550, day: THIS_SAT,     hour: 9.5,  price: 25, energy: 2, loud: .1, buzz: .5, kid: .9, pet: .8, group: [1, 2, 10, 20],   tags: { food: 1, market: 1, outdoor: .6, family: .6 } },
  { id: 17, name: 'Halloween party at Fri-Son',    place: 'Fribourg',   lat: 46.7985, lng: 7.1480, day: HALLOWEEN,    hour: 22,   price: 25, energy: 9, loud: 1,  buzz: .9, kid: 0,  pet: 0,  group: [1, 2, 20, 200],  tags: { halloween: 1, party: 1, music: .8, nightlife: 1, indoor: 1 }, anchor: 'halloween', main: true },
  { id: 18, name: 'Ghost walk through old Fribourg', place: 'Fribourg', lat: 46.8060, lng: 7.1640, day: HALLOWEEN,    hour: 19,   price: 18, energy: 3, loud: .2, buzz: .8, kid: .7, pet: .6, group: [1, 2, 10, 20],   tags: { halloween: 1, tour: 1, culture: .6, outdoor: .8 }, anchor: 'halloween' },
  { id: 19, name: 'Pumpkin patch and carving',     place: 'Kerzers',    lat: 46.9750, lng: 7.1960, day: HALLOWEEN,    hour: 14,   price: 12, energy: 2, loud: .2, buzz: .6, kid: 1,  pet: .7, group: [1, 2, 10, 30],   tags: { halloween: .8, family: 1, outdoor: .7, food: .3 }, anchor: 'halloween' },
  { id: 20, name: 'Autumn Beats festival',         place: 'Fribourg',   lat: 46.7985, lng: 7.1480, day: NEXT_SAT,     hour: 18,   price: 59, energy: 8, loud: 1,  buzz: 1,  kid: .1, pet: 0,  group: [1, 2, 50, 500],  tags: { music: 1, festival: 1, party: .7, nightlife: .8, indoor: .8 }, anchor: 'autumnbeats', main: true },
  { id: 21, name: 'Drum and bass club night',      place: 'Bern',       lat: 46.9490, lng: 7.4400, day: NEXT_SAT - 1, hour: 23,   price: 20, energy: 9, loud: 1,  buzz: .6, kid: 0,  pet: 0,  group: [1, 2, 20, 200],  tags: { music: 1, party: 1, nightlife: 1, techno: .6 } },
  { id: 22, name: 'Acoustic brunch session',       place: 'Fribourg',   lat: 46.8040, lng: 7.1590, day: NEXT_SAT + 1, hour: 11,   price: 15, energy: 2, loud: .2, buzz: .6, kid: .6, pet: .5, group: [1, 2, 6, 12],    tags: { music: 1, food: .6, indoor: 1 } },
  { id: 23, name: 'Saint-Nicolas parade',          place: 'Fribourg',   lat: 46.8063, lng: 7.1630, day: ST_NICOLAS,   hour: 17,   price: 0,  energy: 4, loud: .4, buzz: 1,  kid: 1,  pet: .5, group: [1, 1, 50, 500],  tags: { festival: 1, culture: .9, family: .8, outdoor: 1 }, anchor: 'stnicolas', main: true },
];

// Hand-made semantic neighbourhood: how strongly a word implies a tag
const RELATED = {
  concert:   { music: .9, classical: .7, jazz: .6, festival: .4 },
  music:     { jazz: .7, classical: .7, techno: .7, festival: .5 },
  party:     { nightlife: .9, techno: .8, festival: .6, music: .5, social: .4, halloween: .5 },
  nightlife: { party: .9, comedy: .4, jazz: .4 },
  outdoor:   { nature: .8, hiking: .7, water: .6, festival: .3 },
  nature:    { outdoor: .8, hiking: .8 },
  hike:      { hiking: 1, nature: .7, outdoor: .6 },
  hiking:    { nature: .7, outdoor: .6, adventure: .4 },
  active:    { sport: .9, adventure: .8, climbing: .7, hiking: .7 },
  sport:     { climbing: .8, adventure: .6, hiking: .5, water: .5 },
  relax:     { wellness: .9, yoga: .8, nature: .4 },
  culture:   { museum: .8, art: .8, classical: .6, tour: .5, festival: .4 },
  art:       { festival: .5, museum: .6, culture: .7 },
  food:      { wine: .6, market: .6, tour: .3 },
  drinks:    { wine: .8, nightlife: .6 },
  family:    { kids: 1, science: .4, games: .4, halloween: .4 },
  funny:     { comedy: 1 },
  spooky:    { halloween: 1 },
};
const VOCAB = [...new Set(EVENTS.flatMap(e => Object.keys(e.tags)))].sort();

// Similarity of a user keyword to an event tag, in [0, 1]
function sim(kw, tag) {
  if (kw === tag) return 1;
  if (kw.length >= 3 && (tag.startsWith(kw) || kw.startsWith(tag))) return .95;
  const typo = strSim(kw, tag);
  const rel = Math.max(RELATED[kw]?.[tag] ?? 0, RELATED[tag]?.[kw] ?? 0);
  return Math.max(rel, typo >= .7 ? typo : 0);
}

// ============================================================
//  Linguistic terms: each word is a fuzzy set
// ============================================================
const TERMS = {
  when: {
    tonight:     { label: 'Today',         f: x => trap(x, -1, 0, 0, 1.5) },
    tomorrow:    { label: 'Tomorrow',      f: x => trap(x, 0, 1, 1, 3) },
    thisWeekend: { label: 'This weekend',  f: x => trap(x, THIS_SAT - 2, THIS_SAT, THIS_SAT + 1, THIS_SAT + 2) },
    // Early in the week, "next weekend" is ambiguous: some people mean the coming one
    nextWeekend: { label: 'Next weekend',  f: x => Math.max(trap(x, NEXT_SAT - 2, NEXT_SAT, NEXT_SAT + 1, NEXT_SAT + 2),
                                                             DOW >= 1 && DOW <= 3 ? .4 * trap(x, THIS_SAT - 2, THIS_SAT, THIS_SAT + 1, THIS_SAT + 2) : 0) },
    twoWeeks:    { label: 'In two weeks',  f: x => trap(x, 9, 12, 16, 19) },
    soon:        { label: 'Sometime soon', f: x => shoulder(x, 4, 12) },
    thisMonth:   { label: 'This month',    f: x => shoulder(x, END_OF_MONTH, END_OF_MONTH + 4) },
  },
  time: {
    morning:   { label: 'Morning',    f: h => trap(h, 5, 7, 10, 12),       at: 8.5 },
    afternoon: { label: 'Afternoon',  f: h => trap(h, 11, 13, 16, 18),     at: 14.5 },
    evening:   { label: 'Evening',    f: h => trap(h, 16.5, 18.5, 21, 23), at: 19.75 },
    late:      { label: 'Late night', f: h => trap(h, 20.5, 22.5, 24, 24), at: 23.2 },
  },
  what: {
    music:   { label: 'Music',        kw: ['music'] },
    outdoor: { label: 'Outdoors',     kw: ['outdoor'] },
    food:    { label: 'Food & drink', kw: ['food', 'drinks'] },
    culture: { label: 'Culture',      kw: ['culture'] },
    active:  { label: 'Sport',        kw: ['active'] },
    relax:   { label: 'Relaxing',     kw: ['relax'] },
    party:   { label: 'Party',        kw: ['party'] },
    funny:   { label: 'Comedy',       kw: ['funny'] },
  },
  energy: {
    chill:  { label: 'Chill',      f: x => trap(x, 0, 0, 2, 4),     at: 1 },
    easy:   { label: 'Easy-going', f: x => trap(x, 1, 3, 5, 6.5),   at: 4 },
    lively: { label: 'Lively',     f: x => trap(x, 4, 6, 7.5, 9),   at: 6.75 },
    wild:   { label: 'Wild',       f: x => trap(x, 7, 8.5, 10, 10), at: 9.25 },
  },
  dist: {
    walking:   { label: 'Walking distance', ideal: 2,  max: 5 },
    nearby:    { label: 'Nearby',           ideal: 10, max: 20 },
    shortTrip: { label: 'Short trip',       ideal: 25, max: 45 },
    dayTrip:   { label: 'Day trip',         ideal: 60, max: 100 },
  },
  budget: {
    free:     { label: 'Free',           ideal: 0,   max: 8 },
    cheap:    { label: 'Cheap',          ideal: 20,  max: 35 },
    moderate: { label: 'Not too pricey', ideal: 50,  max: 80 },
    splurge:  { label: 'Splurge',        ideal: 150, max: 250 },
  },
  who: {
    solo:    { label: 'Just me' },
    couple:  { label: 'As a couple' },
    friends: { label: 'With friends' },
    kids:    { label: 'With kids' },
    dog:     { label: 'With my dog' },
  },
};
for (const dim of ['dist', 'budget']) for (const t of Object.values(TERMS[dim])) t.f = x => shoulder(x, t.ideal, t.max);
for (const a of ANCHORS) TERMS.when['around:' + a.key] = { label: 'Around ' + a.name, f: x => trap(x, a.day - 3, a.day - 1, a.day + 1, a.day + 3) };

// Dimensions in the order people think about them. `w` = default importance.
const DIMS = {
  when:   { label: 'When',        w: .9, multi: true },
  time:   { label: 'Time of day', w: .6, multi: true },
  what:   { label: 'What',        w: .9, multi: true },
  energy: { label: 'Vibe',        w: .7, multi: true },
  dist:   { label: 'Distance',    w: .8, multi: false },
  budget: { label: 'Budget',      w: .7, multi: false },
  who:    { label: 'Who',         w: .8, multi: true },
};

// ============================================================
//  Answers: every dimension is optional (empty = skipped)
// ============================================================
const emptyAnswers = () => ({
  text: '', when: [], time: [], what: [], energy: [], dist: [], budget: [], who: [],
  keywords: [], range: null, custom: {}, imp: {}, city: 'fribourg', going: [], best: false,
});
function termFn(dim, t, a) {
  let f;
  if (t.key === 'custom') {
    const n = a.custom[dim];
    f = dim === 'dist' ? x => shoulder(x, n, n * 1.5) : x => shoulder(x, n, n * 1.3 + 5);
  } else if (t.key === 'range') {
    const [s, e] = a.range.map(d => offOf(parseISO(d)));
    f = x => trap(x, s - 2, s, e, e + 2);
  } else f = TERMS[dim][t.key].f;
  const h = t.hedge ? HEDGES[t.hedge].fn : m => m;
  return t.neg ? x => 1 - h(f(x)) : x => h(f(x));
}
// Several terms in one dimension = OR = union (max)
function unionFn(dim, a) {
  const fs = a[dim].map(t => termFn(dim, t, a));
  return x => Math.max(0, ...fs.map(f => f(x)));
}
function termLabel(dim, t, a) {
  let base;
  if (t.key === 'custom') base = dim === 'dist' ? `Within ${a.custom.dist} km` : `Under CHF ${a.custom.budget}`;
  else if (t.key === 'range') base = a.range[0] === a.range[1] ? fmtDay(offOf(parseISO(a.range[0]))) : `${fmtShort(offOf(parseISO(a.range[0])))} – ${fmtShort(offOf(parseISO(a.range[1])))}`;
  else base = TERMS[dim][t.key].label;
  const pre = [t.neg && 'not', t.hedge && HEDGES[t.hedge].label].filter(Boolean).join(' ');
  return pre ? `${pre} ${base[0].toLowerCase()}${base.slice(1)}` : base;
}
function understood(a) {
  const out = [];
  for (const dim of Object.keys(DIMS)) {
    const imp = a.imp[dim] === 1 ? ' (must)' : a.imp[dim] < .5 ? ' (nice to have)' : '';
    for (const t of a[dim]) out.push({ dim, key: t.key, label: termLabel(dim, t, a) + imp });
    if (dim === 'what') for (const k of a.keywords) out.push({ dim: 'keyword', key: k, label: k });
  }
  if (a.city !== 'fribourg' || a.dist.length) out.push({ dim: 'city', key: a.city, label: 'from ' + CITIES[a.city].label });
  for (const g of a.going) { const an = ANCHORS.find(x => x.key === g); if (an) out.push({ dim: 'going', key: g, label: 'going to ' + an.name }); }
  if (a.best) out.push({ dim: 'best', key: 'best', label: 'only the best' });
  return out;
}

function readAnswers(search = location.search) {
  const a = emptyAnswers();
  let s;
  try { s = JSON.parse(new URLSearchParams(search).get('s') || '{}'); } catch { s = {}; }
  for (const dim of Object.keys(DIMS))
    if (Array.isArray(s[dim])) a[dim] = s[dim].filter(t => t && (TERMS[dim][t.key] || t.key === 'custom' || t.key === 'range'));
  if (typeof s.text === 'string') a.text = s.text;
  if (Array.isArray(s.keywords)) a.keywords = s.keywords.filter(k => typeof k === 'string');
  if (Array.isArray(s.range) && s.range.length === 2) a.range = s.range;
  else a.when = a.when.filter(t => t.key !== 'range');
  if (s.custom && typeof s.custom === 'object') a.custom = s.custom;
  if (s.imp && typeof s.imp === 'object') a.imp = s.imp;
  if (CITIES[s.city]) a.city = s.city;
  if (Array.isArray(s.going)) a.going = s.going.filter(g => ANCHORS.some(x => x.key === g));
  a.best = !!s.best;
  return a;
}
const toQuery = a => '?s=' + encodeURIComponent(JSON.stringify(a));

// ============================================================
//  Understanding free text (computing with words, typo tolerant)
// ============================================================
const LEXICON = [
  [['today', 'tonight', 'tonite', 'this evening'], [['when', 'tonight']]],
  [['tomorrow', 'tmrw', 'tmr', 'tomoz'], [['when', 'tomorrow']]],
  [['this weekend', 'weekend', 'wknd', 'this wknd', 'saturday', 'sunday'], [['when', 'thisWeekend']]],
  [['next weekend', 'next wknd'], [['when', 'nextWeekend']]],
  [['in two weeks', 'in 2 weeks', 'two weeks', '2 weeks', 'fortnight'], [['when', 'twoWeeks']]],
  [['soon', 'next few days', 'this week', 'asap'], [['when', 'soon']]],
  [['this month', 'end of the month'], [['when', 'thisMonth']]],
  [['halloween'], [['when', 'around:halloween']]],
  [['saint nicolas', 'st nicolas', 'nicolas', 'saint nick'], [['when', 'around:stnicolas']]],
  [['autumn beats'], [['when', 'around:autumnbeats']]],
  [['morning', 'breakfast'], [['time', 'morning']]],
  [['afternoon', 'lunch', 'daytime'], [['time', 'afternoon']]],
  [['evening', 'after work'], [['time', 'evening']]],
  [['late', 'late night', 'night', 'midnight'], [['time', 'late']]],
  [['music', 'concert', 'gig', 'live music', 'band'], [['what', 'music']]],
  [['outdoors', 'outdoor', 'outside', 'nature', 'fresh air'], [['what', 'outdoor']]],
  [['food', 'eat', 'eating', 'brunch', 'dinner', 'drinks', 'foodie'], [['what', 'food']]],
  [['culture', 'museum', 'art', 'theatre', 'theater', 'history'], [['what', 'culture']]],
  [['sport', 'sporty', 'workout', 'exercise'], [['what', 'active']]],
  [['active'], [['what', 'active'], ['energy', 'lively']]],
  [['relaxing', 'relax', 'wellness', 'spa', 'unwind'], [['what', 'relax']]],
  [['party', 'dance', 'dancing', 'club', 'clubbing', 'rave'], [['what', 'party']]],
  [['comedy', 'funny', 'laugh', 'stand up'], [['what', 'funny']]],
  [['chill', 'chilled', 'calm', 'quiet', 'cozy', 'cosy', 'lazy', 'mellow'], [['energy', 'chill']]],
  [['easy going', 'easygoing', 'laid back', 'low key', 'relaxed'], [['energy', 'easy']]],
  [['lively', 'social', 'buzzing', 'upbeat', 'fun'], [['energy', 'lively']]],
  [['wild', 'crazy', 'intense', 'loud', 'energetic', 'adventurous', 'big night'], [['energy', 'wild']]],
  [['walking distance', 'walkable', 'around the corner', 'on foot'], [['dist', 'walking']]],
  [['nearby', 'near', 'close', 'close by', 'not too far', 'not far', 'local'], [['dist', 'nearby']]],
  [['short trip', 'short drive', 'quick trip'], [['dist', 'shortTrip']]],
  [['day trip', 'road trip', 'far away'], [['dist', 'dayTrip']]],
  [['free', 'for free', 'no cost', 'gratis'], [['budget', 'free']]],
  [['cheap', 'budget', 'affordable', 'inexpensive', 'not expensive', 'low cost', 'broke'], [['budget', 'cheap']]],
  [['not too expensive', 'not too pricey', 'reasonable', 'mid range', 'moderate'], [['budget', 'moderate']]],
  [['expensive', 'fancy', 'splurge', 'treat myself', 'posh'], [['budget', 'splurge']]],
  [['alone', 'by myself', 'solo', 'just me', 'on my own'], [['who', 'solo']]],
  [['date', 'date night', 'partner', 'girlfriend', 'boyfriend', 'wife', 'husband', 'couple', 'two of us'], [['who', 'couple']]],
  [['friends', 'mates', 'group', 'gang', 'buddies', 'crew'], [['who', 'friends']]],
  [['kids', 'children', 'family', 'kid', 'son', 'daughter', 'toddler'], [['who', 'kids']]],
  [['dog', 'pup', 'puppy', 'pet', 'doggo'], [['who', 'dog']]],
  [['fribourg', 'freiburg'], [['city', 'fribourg']]],
  [['bern', 'berne'], [['city', 'bern']]],
  [['murten', 'morat'], [['city', 'murten']]],
  [['bulle'], [['city', 'bulle']]],
  [['best', 'top', 'coolest', 'highlights', 'must see', 'unmissable'], [['best', true]]],
];
const MODIFIERS = {
  very: ['very', 'really', 'super', 'extremely', 'totally'],
  somewhat: ['somewhat', 'kind of', 'kinda', 'sort of', 'fairly', 'roughly', 'a bit', 'slightly', 'quite'],
  not: ['not', 'no', 'nothing', 'without'],
  must: ['must', 'must be', 'definitely', 'only', 'has to be', 'need'],
  nice: ['ideally', 'maybe', 'preferably', 'if possible', 'perhaps', 'possibly'],
};
const STOPWORDS = new Set(('i im id want wanna to do something some thing things a an the with and or for in on at of my me we us our go going ' +
  'out get like would feel feeling mood this that it is be are show find any anything event events please can you from but too so just ' +
  'also have has what where when who how let lets around about up down there here time day days week weeks ok okay ' +
  'under below less than max within').split(' '));

function parseQuery(text) {
  const out = { items: [], keywords: [], custom: {}, imp: {}, city: null, best: false, fixes: [], ignored: [] };
  let s = ' ' + text.toLowerCase() + ' ';
  const kmMatch = s.match(/(\d+)\s*(km|kilomet\w*)/);
  if (kmMatch) { out.items.push({ dim: 'dist', key: 'custom' }); out.custom.dist = +kmMatch[1]; s = s.replace(kmMatch[0], ' '); }
  const money = s.match(/(?:chf|fr\.?|francs?)\s*(\d+)|(\d+)\s*(?:chf|fr\b|francs?|bucks)/);
  if (money) { out.items.push({ dim: 'budget', key: 'custom' }); out.custom.budget = +(money[1] || money[2]); s = s.replace(money[0], ' '); }

  const words = s.replace(/[^a-z0-9äöüéèàç\s]/g, ' ').split(/\s+/).filter(Boolean);
  const ish = new Set();
  words.forEach((w, i) => { if (w.length > 5 && w.endsWith('ish')) { words[i] = w.slice(0, -3); ish.add(i); } });

  // Collect every phrase that roughly matches somewhere, then keep the longest, closest ones
  const need = w => w.length <= 4 ? 1 : w.length <= 6 ? .8 : .75;
  const cands = [];
  for (const [phrases, effects] of LEXICON) for (const p of phrases) {
    const pw = p.split(' '), k = pw.length;
    for (let i = 0; i + k <= words.length; i++) {
      // every word of the phrase has to be close, so "tmrw evening" is not "this evening"
      const sims = pw.map((w, j) => strSim(words[i + j], w));
      if (sims.some((v, j) => v < need(pw[j]))) continue;
      cands.push({ i, k, sc: Math.min(...sims), p, got: words.slice(i, i + k).join(' '), effects });
    }
  }
  cands.sort((x, y) => y.k - x.k || y.sc - x.sc);
  const used = Array(words.length).fill(false);
  const isMod = (kind, j) => MODIFIERS[kind].includes(words[j]) ? 1 : j > 0 && MODIFIERS[kind].includes(words[j - 1] + ' ' + words[j]) ? 2 : 0;
  for (const c of cands) {
    if (used.slice(c.i, c.i + c.k).some(Boolean)) continue;
    for (let j = c.i; j < c.i + c.k; j++) used[j] = true;
    if (c.sc < 1) out.fixes.push([c.got, c.p]);
    // Look back a few words for hedges, negation and importance
    let hedge = ish.has(c.i + c.k - 1) ? 'somewhat' : undefined, neg = false, imp;
    for (let j = c.i - 1; j >= Math.max(0, c.i - 4) && !used[j]; j--) {
      let n;
      if ((n = isMod('very', j))) hedge = 'very';
      else if ((n = isMod('somewhat', j))) hedge = 'somewhat';
      else if ((n = isMod('not', j))) neg = true;
      else if ((n = isMod('must', j))) imp = 1;
      else if ((n = isMod('nice', j))) imp = .4;
      else if (STOPWORDS.has(words[j])) continue;
      else break;
      for (let q = 0; q < n; q++) used[j - q] = true;
      j -= n - 1;
    }
    for (const [dim, key] of c.effects) {
      if (dim === 'city') out.city = key;
      else if (dim === 'best') out.best = true;
      else if (TERMS[dim][key]) {
        if (!out.items.some(t => t.dim === dim && t.key === key)) out.items.push({ dim, key, hedge, neg });
        if (imp) out.imp[dim] = imp;
      }
    }
  }
  // Leftover words: specific interests like "jazz" or "yoga", typos allowed
  const known = [...new Set([...VOCAB, ...Object.keys(RELATED)])];
  words.forEach((w, i) => {
    if (used[i] || STOPWORDS.has(w) || Object.values(MODIFIERS).flat().includes(w) || w.length < 3 || /^\d+$/.test(w)) return;
    const [best, sc] = known.map(k => [k, strSim(w, k)]).sort((x, y) => y[1] - x[1])[0];
    if (sc >= .75) { if (!out.keywords.includes(best)) out.keywords.push(best); if (sc < 1) out.fixes.push([w, best]); }
    else out.ignored.push(w);
  });
  return out;
}
// Text wins for any dimension it mentions; everything else keeps what was tapped
function mergeParsed(base, p, text) {
  const a = JSON.parse(JSON.stringify(base));
  a.text = text;
  for (const dim of Object.keys(DIMS)) {
    const items = p.items.filter(t => t.dim === dim).map(({ key, hedge, neg }) => ({ key, ...(hedge && { hedge }), ...(neg && { neg }) }));
    if (items.length) a[dim] = DIMS[dim].multi ? items : items.slice(-1);
  }
  if (p.keywords.length) a.keywords = p.keywords;
  Object.assign(a.custom, p.custom);
  Object.assign(a.imp, p.imp);
  if (p.city) a.city = p.city;
  if (p.best) a.best = true;
  return a;
}

// ============================================================
//  Learning over time: tag affinities from "more like this" / "not for me"
// ============================================================
const PROFILE_KEY = 'fuzzy-event-finder-profile';
function loadProfile() {
  try {
    const p = JSON.parse(localStorage.getItem(PROFILE_KEY));
    if (p && p.aff) return { aff: p.aff, liked: p.liked || [], hidden: p.hidden || [] };
  } catch {}
  return { aff: {}, liked: [], hidden: [] };
}
function saveProfile(p) { try { localStorage.setItem(PROFILE_KEY, JSON.stringify(p)); } catch {} }
function giveFeedback(p, e, sign) {
  for (const [t, d] of Object.entries(e.tags)) p.aff[t] = Math.max(-1, Math.min(1, (p.aff[t] || 0) + .35 * sign * d));
  p.liked = p.liked.filter(id => id !== e.id);
  p.hidden = p.hidden.filter(id => id !== e.id);
  (sign > 0 ? p.liked : p.hidden).push(e.id);
  saveProfile(p);
}
function taste(p, e) {
  let s = 0, n = 0;
  for (const [t, d] of Object.entries(e.tags)) { s += (p.aff[t] || 0) * d; n += d; }
  return clamp01(.5 + .5 * s / n);
}

// ============================================================
//  Model: criteria + fuzzy rules that connect them
// ============================================================
function groupSize(who) {
  const k = new Set(who.map(t => t.key));
  const adults = k.has('friends') ? 4 : k.has('couple') ? 2 : k.has('solo') ? 1 : 2;
  return adults + (k.has('kids') ? 2 : 0);
}

function buildModel(a, profile = loadProfile()) {
  const center = CITIES[a.city];
  const distOf = e => km(center, e);
  const keywords = [...new Set([...a.what.flatMap(t => TERMS.what[t.key].kw), ...a.keywords])];
  const going = ANCHORS.filter(x => a.going.includes(x.key));
  const kids = a.who.some(t => t.key === 'kids'), dog = a.who.some(t => t.key === 'dog');
  const size = groupSize(a.who);
  const imp = d => a.imp[d] ?? DIMS[d].w;
  const f = Object.fromEntries(['when', 'time', 'energy', 'dist', 'budget'].map(d => [d, unionFn(d, a)]));
  const active = {
    when: a.when.length > 0, time: a.time.length > 0, what: keywords.length > 0, energy: a.energy.length > 0,
    dist: a.dist.length > 0, budget: a.budget.length > 0, who: a.who.length > 0, plans: going.length > 0,
  };

  const loudness = e => Math.max(e.loud, rise(e.energy, 6, 9));
  const lateness = e => trap(e.hour, 19, 21, 24, 24);
  const exceptional = e => rise(e.buzz, .75, .95);
  // How well the event fits if the wanted period were a few days later (fades with the delay)
  const justAfter = e => { let m = 0; for (let k = 1; k <= 7; k++) m = Math.max(m, f.when(e.day - k) * (1 - k / 8)); return m; };

  // Fuzzy IF-THEN rules: firing strength = min of the antecedents
  const rules = {
    recovery: {
      name: 'Recovery', active: active.plans,
      text: `IF you're going to ${going.map(g => g.name).join(' or ') || 'a big event'} AND an event is within a day or two of it AND it's loud THEN it fits your plans less`,
      off: 'Not active: tell us about an event you are already going to.',
      fire: e => Math.max(0, ...going.map(g => Math.min(trap(Math.abs(e.day - g.day), -1, 0, 1, 2.5), loudness(e), g.loud))),
    },
    worthWait: {
      name: 'Worth the wait', active: active.when,
      text: 'IF an event is exceptional AND it is just after the time you asked for THEN it still counts for when',
      off: 'Not active: you did not say when.',
      fire: e => Math.min(exceptional(e), justAfter(e)),
    },
    kidsLate: {
      name: 'Kids and late nights', active: kids,
      text: 'IF you are bringing kids AND the event starts late THEN it suits your group less',
      off: 'Not active: you are not bringing kids.',
      fire: e => kids ? lateness(e) : 0,
    },
  };

  const energyCenter = active.energy ? centroid(f.energy, 0, 10) : 5;
  const criteria = [
    active.when && { key: 'when', label: 'When', w: imp('when'),
      mu: e => Math.max(f.when(e.day), .7 * rules.worthWait.fire(e)),
      why: e => `${relDay(e.day)} is a bit outside your time` },
    active.time && { key: 'time', label: 'Time', w: imp('time'),
      mu: e => f.time(e.hour), why: e => `starts at ${fmtHour(e.hour)}` },
    active.what && { key: 'what', label: 'What', w: imp('what'),
      mu: e => Math.max(...keywords.map(k => Math.max(0, ...Object.entries(e.tags).map(([t, d]) => sim(k, t) * d)))),
      why: () => 'not quite what you asked for' },
    active.energy && { key: 'energy', label: 'Vibe', w: imp('energy'),
      mu: e => f.energy(e.energy), why: e => e.energy > energyCenter ? 'livelier than you wanted' : 'calmer than you wanted' },
    active.dist && { key: 'dist', label: 'Where', w: imp('dist'),
      mu: e => f.dist(distOf(e)), why: e => `${distOf(e).toFixed(0)} km away` },
    active.budget && { key: 'budget', label: 'Cost', w: imp('budget'),
      mu: e => f.budget(e.price), why: e => `costs CHF ${e.price}` },
    active.who && { key: 'who', label: 'Who', w: imp('who'),
      mu: e => Math.min(trap(size, ...e.group), kids ? e.kid : 1, dog ? e.pet : 1, 1 - .8 * rules.kidsLate.fire(e)),
      why: e => kids && rules.kidsLate.fire(e) > .5 ? 'late for kids' : kids && e.kid < .5 ? 'not very kid-friendly'
        : dog && e.pet < .5 ? 'not dog-friendly' : 'not ideal for your group' },
    active.plans && { key: 'plans', label: 'Plans', w: .9,
      mu: e => 1 - .85 * rules.recovery.fire(e), why: () => 'loud and right next to your other plans' },
  ].filter(Boolean);

  // Fit = compensatory AND over the answered criteria (skipped ones don't count):
  // half Yager's weighted min (the weakest answer matters), half weighted mean (people trade off).
  // Match also folds in how exceptional the event is and what we've learned about your taste.
  const wSum = criteria.reduce((s, c) => s + c.w, 0);
  const results = EVENTS.filter(e => !(e.main && a.going.includes(e.anchor))).map(e => {
    const vals = criteria.map(c => clamp01(c.mu(e)));
    const wMin = Math.min(...vals.map((v, i) => Math.max(1 - criteria[i].w, v)));
    const wMean = vals.reduce((s, v, i) => s + criteria[i].w * v, 0) / wSum;
    const fit = vals.length ? .5 * wMin + .5 * wMean : 1;
    const appeal = .5 * e.buzz + .5 * taste(profile, e);
    const k = a.best || !criteria.length ? .5 : .3;
    let match = fit * (1 - k + k * appeal);
    if (!active.when) match *= .8 + .2 * shoulder(e.day, 10, 40); // no date given: sooner is a little better
    if (profile.hidden.includes(e.id)) match *= .3;
    const inTime = active.when ? f.when(e.day) : 1;
    return { e, vals, fit, match, inTime, crisp: vals.every(v => v >= .999),
      worthWait: active.when && .7 * rules.worthWait.fire(e) > inTime + .05,
      liked: profile.liked.includes(e.id), hidden: profile.hidden.includes(e.id) };
  }).sort((x, y) => y.match - x.match);

  // Things a friend would tell you
  const insights = [];
  for (const g of going)
    insights.push({ text: `You're going to ${g.name} ${relDay(g.day)}, so we're ranking loud, high-energy events right around it lower. You'll want some energy left for it.` });
  if (active.when) {
    const whenText = a.when.map(t => termLabel('when', t, a).toLowerCase()).join(' or ');
    const bestInTime = results.find(r => r.inTime >= .5)?.match ?? 0;
    const wait = results.find(r => r.worthWait && r.match >= .4);
    if (wait && bestInTime < .5)
      insights.push({ text: `Not much fits ${whenText}, but ${wait.e.name} ${relDay(wait.e.day)} is worth the wait.` });
    else if (wait)
      insights.push({ text: `${wait.e.name} (${relDay(wait.e.day)}) is just outside ${whenText}, but it's one of the best events around, so we kept it in.` });
  }
  const soon = ANCHORS.find(x => x.day >= 0 && x.day <= 7 && !a.going.includes(x.key) && !a.when.some(t => t.key === 'around:' + x.key));
  if (soon) insights.push({ text: `Heads up: ${soon.name} is ${relDay(soon.day)}.`, action: { label: `Show ${soon.name} events`, when: 'around:' + soon.key } });

  return { a, center, distOf, keywords, going, kids, dog, size, f, active, rules, criteria, results, insights, profile, energyCenter, loudness };
}

// ============================================================
//  Membership-function plot (SVG)
// ============================================================
function plot(svg, o) {
  const W = 360, H = o.height || 116, P = { l: 18, r: 10, t: 20, b: 18 };
  const sx = x => P.l + (x - o.xmin) / (o.xmax - o.xmin) * (W - P.l - P.r);
  const sy = y => P.t + (1 - y) * (H - P.t - P.b);
  let s = '';
  s += `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(1)}" y2="${sy(1)}"/>`;
  s += `<line class="axis" x1="${P.l}" x2="${W - P.r}" y1="${sy(0)}" y2="${sy(0)}"/>`;
  s += `<text class="ylab" x="2" y="${sy(1) + 3}">1</text><text class="ylab" x="2" y="${sy(0) + 3}">0</text>`;
  for (const mk of o.markers || []) {
    if (mk.x < o.xmin || mk.x > o.xmax) continue;
    s += `<line class="marker" x1="${sx(mk.x)}" x2="${sx(mk.x)}" y1="${sy(1) - 4}" y2="${sy(0)}"/>`;
    s += `<text class="mlabel" x="${sx(mk.x)}" y="${P.t - 9}">${mk.label}</text>`;
  }
  const N = 240;
  for (const c of o.curves) {
    const pts = [];
    for (let i = 0; i <= N; i++) { const x = o.xmin + (o.xmax - o.xmin) * i / N; pts.push([sx(x), sy(c.f(x))]); }
    const d = 'M' + pts.map(p => p.map(v => v.toFixed(1)).join(',')).join('L');
    if (!c.faint) s += `<path class="area" d="${d}L${sx(o.xmax)},${sy(0)}L${sx(o.xmin)},${sy(0)}Z"/>`;
    s += `<path class="curve${c.faint ? ' faint' : ''}" d="${d}"/>`;
    if (c.label) s += `<text class="term${c.on ? ' on' : ''}" x="${sx(c.at)}" y="${sy(1) - 4}">${c.label}</text>`;
  }
  for (const t of o.ticks || []) s += `<text class="tick" x="${sx(t[0])}" y="${H - 4}">${t[1]}</text>`;
  if (o.marker != null) s += `<line class="marker" x1="${sx(o.marker)}" x2="${sx(o.marker)}" y1="${sy(1) - 2}" y2="${sy(0)}"/>`;
  for (const p of o.points || []) {
    const x = Math.max(o.xmin, Math.min(o.xmax, p.x));
    s += `<circle class="dot" cx="${sx(x)}" cy="${sy(p.y)}" r="4.5" fill="${scoreColor(p.y)}"><title>${p.title}</title></circle>`;
  }
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.innerHTML = s;
}
