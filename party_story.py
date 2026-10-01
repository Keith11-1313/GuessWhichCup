"""Ten short chapters of a night at the Lantern House."""

CHAPTERS = (
    (
        "An invitation",
        "Mira: Welcome to Lantern House. Find the spark and join the party.",
    ),
    (
        "The kitchen crew",
        "Mira: The snacks can wait. Theo wants to see your next trick.",
    ),
    (
        "A little competition",
        "Theo: Three cups, one spark. Keep your eyes on the table.",
    ),
    ("Room for one more", "Jun: Another guest, another cup. Can you keep up?"),
    ("The party trick", "Jun: Nobody knows how Mira keeps that little spark glowing."),
    (
        "Behind the lanterns",
        "Mira: It is our first-party wish. We keep it safe together.",
    ),
    ("Midnight guests", "Theo: The whole room is watching now. No pressure, right?"),
    ("One last song", "Jun: The music is winding down. Bring that spark home."),
    ("The final table", "Mira: Six cups. One wish. You have come a long way tonight."),
    (
        "A wish to keep",
        "Mira: Find it one last time. There is always a seat here for you.",
    ),
)

# Location, speaker, and two short dialogue beats. Read at the player's pace.
SCENES = (
    (
        "hall",
        "Mira",
        "You made it. I kept a seat for you.",
        "This spark holds a wish. Help me keep it safe tonight.",
    ),
    (
        "hall",
        "Theo",
        "Everyone brought a wish to the party.",
        "Mira has not told us hers. Let us earn her trust.",
    ),
    (
        "hall",
        "Mira",
        "The spark is still bright. You have a steady eye.",
        "Come into the kitchen. Jun is waiting for us.",
    ),
    (
        "kitchen",
        "Jun",
        "I added a cup. The party is getting crowded.",
        "Mira used to host these nights with her brother.",
    ),
    (
        "kitchen",
        "Theo",
        "He moved away last spring. The house went quiet.",
        "Tonight is the first time she has invited everyone back.",
    ),
    (
        "kitchen",
        "Mira",
        "I wished this place would feel like home again.",
        "You are all still here. Maybe the wish is already working.",
    ),
    (
        "terrace",
        "Jun",
        "Midnight. Bring the lantern out onto the terrace.",
        "One gust and the spark goes dark. Stay with it.",
    ),
    (
        "terrace",
        "Theo",
        "My wish? That we do this again next year.",
        "Keep the spark moving. We are almost there.",
    ),
    (
        "terrace",
        "Mira",
        "I was afraid everyone had forgotten this place.",
        "You proved me wrong. One last table before sunrise.",
    ),
    (
        "dawn",
        "Mira",
        "The sky is turning gold. The last wish is yours.",
        "Find the spark, and let us carry it into morning.",
    ),
)


def location(mode, level):
    if mode == "Endless":
        return "afterparty"
    return SCENES[min(10, max(1, level)) - 1][0]


LOCATION_NAMES = {
    "hall": "Welcome hall",
    "kitchen": "The kitchen",
    "terrace": "Midnight terrace",
    "dawn": "Sunrise",
    "afterparty": "Neon afterparty",
}
