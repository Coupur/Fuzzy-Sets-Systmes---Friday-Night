FRIDAY NIGHT

A fuzzy event recommender for Bern, made for the Fuzzy Sets & Systems course. You answer a few
questions about when you're free, your budget, where you start, your energy, what you're into and
who's coming, and it ranks events by how well they fit, using fuzzy membership functions instead of
hard filters.


RUN IT

python -m pip install -r requirements.txt
python app.py

Then open http://127.0.0.1:5000 in your browser.


HOW IT WORKS

The website (event-search/filters.html) asks the questions in 5 steps and sends the answers to
app.py. Every event then gets a score from 0 to 1 for each question: energy, time, keywords and
the date filter are Marlene's functions, money, group size and the kids rating are Fiona's, and the
trip (distance, best way to get there, cost and effort compared to your energy) is Sam's. Each
"How much it matters" slider changes how strict that membership function is. Fiona's relevance
score multiplies all the scores together, and the events are shown best first.

app.py                             connects the website to the Python code
event-search/filters.html          the website
Fuzzy/event_data.py                all events (made up and real Bern events)
Fuzzy/marlenes_part.py             energy, time, keyword and date functions
Fuzzy/fionas_part.py               money, group size and kids functions, and the ranking
Fuzzy/Samuels_Fuzzy_Functions.py   trip planning (distance, transport, effort)
notebooks/                         the notebooks with plots of the membership functions

Each file in Fuzzy/ can be run on its own to test it, for example: python Fuzzy/fionas_part.py


# Contributions
Sam:
Github
Front end / UI
membership fuctions - Distance
Link ui and notbook
Google Doc


Fiona:
membership fuctions - Money
membership fuctions - Group Size Kids
Calc score
list score
Sample Data
Google Doc


Marlene:
membership fuctions - Energy
membership fuctions - Time/Date
Keyword Calculations
Google Doc set up docuemntation
Evaluation form
