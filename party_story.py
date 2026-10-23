"""One short, player-paced story line before each chapter."""

# Title, location, speaker, dialogue. Characters appear only in the writing.
CHAPTERS = (
    ("An invitation", "hall", "Mira", "I saved you a seat. Keep this lucky coin safe."),
    ("The kitchen crew", "hall", "Theo", "Mira brought the coin. I brought snacks. Your turn."),
    ("A little competition", "hall", "Mira", "Steady eyes. Jun is waiting for us in the kitchen."),
    ("Room for one more", "kitchen", "Jun", "Mira's brother moved away. Tonight, her house feels alive again."),
    ("The party trick", "kitchen", "Theo", "Her wish? For this place to feel like home again."),
    ("Behind the lanterns", "kitchen", "Mira", "With you, Theo and Jun here, it already does."),
    ("Midnight guests", "terrace", "Jun", "Bring the coin outside. The next table is on the terrace."),
    ("One last song", "terrace", "Theo", "I wish we could all do this again next year."),
    ("The final table", "terrace", "Mira", "I thought everyone had forgotten this place. You proved me wrong."),
    ("A wish to keep", "dawn", "Mira", "Find the lucky coin once more. This wish is yours."),
)


def location(mode, level):
    if mode == "Endless":
        return "afterparty"
    return CHAPTERS[min(10, max(1, level)) - 1][1]


LOCATION_NAMES = {
    "hall": "Welcome hall",
    "kitchen": "The kitchen",
    "terrace": "Midnight terrace",
    "dawn": "Sunrise",
    "afterparty": "Neon afterparty",
}
