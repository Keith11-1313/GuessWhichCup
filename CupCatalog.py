"""Cup names, rarity odds and the story-only starter. No rendering or saves."""

Starter = ("starter", "Plain Cup", "Starter", 0, "#c7c3b7")
# Single draw and boosted ten-draw rarity weights, out of 10,000.
Rarities = (
    ("Normal", 5000, 3500, "#e2ad62"),
    ("Uncommon", 2700, 3200, "#92cfac"),
    ("Rare", 1500, 2200, "#91bde8"),
    ("Epic", 600, 800, "#c49aef"),
    ("Legendary", 180, 250, "#ffdd92"),
    ("Mythic", 20, 50, "#95f4ed"),
)
Designs = (
    (("normal", "Brass Keepsake"), ("wood", "Oak Tumbler"), ("cream", "Cream Ceramic")),
    (("uncommon", "Garden Glaze"), ("fern", "Fernstone"), ("cobalt", "Cobalt Glaze")),
    (("rare", "Moon Porcelain"), ("tide", "Tideglass"), ("rose", "Rose Quartz")),
    (("epic", "Violet Sigil"), ("ember", "Ember Sigil"), ("jade", "Jade Serpent")),
    (
        ("legendary", "Sun Crown"),
        ("royal", "Royal Hourglass"),
        ("phoenix", "Phoenix Crest"),
    ),
    (("mythic", "Astral Eclipse"), ("void", "Void Bloom"), ("aurora", "Aurora Prism")),
)
Cups = tuple(
    (Skin, Name, Rarity, Weight // 3 + (Index < Weight % 3), Color)
    for (Rarity, Weight, Ignored, Color), Designs in zip(Rarities, Designs)
    for Index, (Skin, Name) in enumerate(Designs)
)
AllCups = (Starter,) + Cups
