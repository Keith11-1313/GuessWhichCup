"""One short, player-paced story line before each chapter."""

# Title, location, speaker, dialogue. Characters appear only in the writing.
Chapters = (
    (
        "The Last Lantern",
        "hall",
        "Mira",
        "Ten tables. One lucky coin. Clear them all and Brass Keepsake is yours.",
    ),
    (
        "Theo's challenge",
        "hall",
        "Theo",
        "One mark earned. I taught Mira this trick. Now try following my cup.",
    ),
    (
        "The invitation",
        "hall",
        "Mira",
        "Two marks on your invitation. Clear my table and Jun will let you into the kitchen.",
    ),
    (
        "A fourth cup",
        "kitchen",
        "Jun",
        "Three marks earned. I've added a cup. Watch the coin before I shuffle.",
    ),
    (
        "The halfway table",
        "kitchen",
        "Theo",
        "Win this one and you're halfway. The kitchen crowd is cheering for you.",
    ),
    (
        "Out into the night",
        "kitchen",
        "Mira",
        "Five marks. Clear this table and we'll take the game out to the terrace.",
    ),
    (
        "Under the lanterns",
        "terrace",
        "Jun",
        "Six marks. Five cups on the terrace. Take a breath, then follow the coin.",
    ),
    (
        "Theo's last trick",
        "terrace",
        "Theo",
        "Seven marks. Nobody has won the trophy cup tonight. Let's change that.",
    ),
    (
        "Before sunrise",
        "terrace",
        "Mira",
        "Eight marks. Beat this table to earn your place in the sunrise final.",
    ),
    (
        "The final coin",
        "dawn",
        "Mira",
        "Nine marks. Six cups. Find the final coin and take Brass Keepsake home.",
    ),
)


def Location(Mode, Level):
    if Mode == "Endless":
        return "afterparty"
    return Chapters[min(10, max(1, Level)) - 1][1]


LocationNames = {
    "hall": "Welcome hall",
    "kitchen": "The kitchen",
    "terrace": "Midnight terrace",
    "dawn": "Sunrise",
    "afterparty": "Neon afterparty",
}
