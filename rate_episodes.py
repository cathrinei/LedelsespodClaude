"""
rate_episodes.py — Episodedata for denne raterunden.
Kjøres én gang og kan slettes etter bruk.
"""

from rate_runner import run

UPDATES = {

    ("topplederpodcast (meyerhaugen)", "sundby"): (
        "Siv Jensen, Petter Meyer", "Christoffer Sundby",
        "Kundelojalitet, merkevarebygging, lederskap fra toppidrett",
        4, "Spenn-CEO om lojalitet og vekst — toppidrettsbakgrunn gir ledervinkel, men business er hovemotiv",
        "personalledelse"),
}

REMOVE_KEYWORDS = []

run(UPDATES, REMOVE_KEYWORDS)
