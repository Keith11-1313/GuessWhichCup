"""Original fine-grid pixel sprites and party scenery; no third-party runtime."""

import tkinter
import turtle
from party_story import location

INK = "#1b1425"


def brass_shading(x, y, left, right):
    """Choose one brass shade from the silhouette edge and light direction."""
    if x in (left, right) or y in (3, 30):
        return INK
    if x <= left + 2:
        return "#ffe4a6"
    if x <= left + 5:
        return "#f5cb7c"
    if x >= right - 3:
        return "#995335"
    if x >= right - 6:
        return "#ba7643"
    return "#dda456"


def register_cup(screen):
    image = tkinter.PhotoImage(width=32, height=34, master=screen.getcanvas())
    for y in range(3, 31):
        inset = max(0, (29 - y) // 7)
        left, right = 5 + inset, 26 - inset
        for x in range(left, right + 1):
            color = brass_shading(x, y, left, right)
            if y in (7, 8, 24, 25) and left + 3 < x < right - 3:
                color = "#edbb6c" if y in (7, 24) else "#c28a46"
            if 11 <= y <= 21 and x in (13, 18):
                color = "#bf813f"
            if 13 <= y <= 19 and x in (14, 17):
                color = "#f0c274"
            if y in (11, 21) and 14 <= x <= 17:
                color = "#bf813f"
            image.put(color, (x, y))
    for y in range(29, 33):
        for x in range(3, 29):
            image.put(
                (
                    INK
                    if y in (29, 32) or x in (3, 28)
                    else ("#ffe0a0" if y == 30 else "#c0884d")
                ),
                (x, y),
            )
    party_images = [image, image.zoom(3), image.zoom(5)]
    screen.register_shape("party_cup", turtle.Shape("image", party_images[1]))
    screen.register_shape("hero_cup", turtle.Shape("image", party_images[2]))
    palettes = {
        "normal": (
            "#ffe4a6",
            "#f5cb7c",
            "#995335",
            "#ba7643",
            "#dda456",
            "#edbb6c",
            "#c28a46",
            "#bf813f",
            "#f0c274",
            "#ffe0a0",
            "#c0884d",
        ),
        "uncommon": (
            "#d9ffe1",
            "#b3e5ba",
            "#325f52",
            "#497d64",
            "#84b899",
            "#a2d8ac",
            "#619c80",
            "#487e65",
            "#b9e6bf",
            "#def8d7",
            "#609775",
        ),
        "rare": (
            "#e4f4ff",
            "#b9d7ed",
            "#344775",
            "#506da0",
            "#88aed1",
            "#b6d4ee",
            "#638abd",
            "#466497",
            "#d7eafa",
            "#e3f5ff",
            "#708fb6",
        ),
        "epic": (
            "#f3daff",
            "#d6b2ed",
            "#563778",
            "#7a4e9e",
            "#ac82c9",
            "#cda4e7",
            "#9265b6",
            "#724899",
            "#e6c6ff",
            "#f6dfff",
            "#9767b7",
        ),
        "legendary": (
            "#ffffde",
            "#ffefad",
            "#a56c27",
            "#cb9239",
            "#f4ce6e",
            "#ffeaa1",
            "#deb453",
            "#ad802d",
            "#fff7bd",
            "#fffbd6",
            "#c59d42",
        ),
        "mythic": (
            "#bbfff0",
            "#82dcd6",
            "#172639",
            "#274655",
            "#426975",
            "#5fa2a9",
            "#346575",
            "#1b475b",
            "#95eee4",
            "#bcfff1",
            "#437784",
        ),
    }
    source = palettes["normal"]
    skin_images = {}
    for skin, colors in palettes.items():
        art = tkinter.PhotoImage(width=32, height=34, master=screen.getcanvas())
        mapping = dict(zip(source, colors))
        for y in range(34):
            for x in range(32):
                if not image.transparency_get(x, y):
                    original = "#%02x%02x%02x" % image.get(x, y)
                    art.put(mapping.get(original, original), (x, y))
        # Distinct engraved symbols; no differences between cups in a round.
        if skin != "normal":
            motif = {
                "uncommon": (
                    (15, 13),
                    (14, 14),
                    (16, 14),
                    (14, 15),
                    (17, 15),
                    (15, 16),
                    (16, 17),
                    (15, 18),
                ),
                "rare": (
                    (16, 12),
                    (14, 13),
                    (13, 14),
                    (13, 16),
                    (14, 18),
                    (16, 19),
                    (17, 18),
                ),
                "epic": (
                    (15, 12),
                    (14, 14),
                    (16, 14),
                    (13, 16),
                    (17, 16),
                    (14, 18),
                    (16, 18),
                    (15, 20),
                ),
                "legendary": (
                    (15, 12),
                    (12, 15),
                    (18, 15),
                    (15, 18),
                    (14, 14),
                    (15, 14),
                    (16, 14),
                    (14, 15),
                    (15, 15),
                    (16, 15),
                    (15, 16),
                ),
                "mythic": (
                    (15, 12),
                    (14, 13),
                    (16, 13),
                    (13, 14),
                    (17, 14),
                    (13, 16),
                    (17, 16),
                    (14, 17),
                    (16, 17),
                    (15, 18),
                ),
            }[skin]
            for x, y in motif:
                art.put(colors[0], (x, y))
        if skin == "legendary":
            for x in (9, 15, 21):
                for y in range(1, 5):
                    art.put(colors[0] if x == 15 else colors[4], (x, y))
            for x in range(9, 22):
                art.put(colors[4], (x, 4))
        elif skin == "mythic":
            for x in range(2, 30):
                y = 20 - (x // 4)
                if x < 8 or x > 24:
                    art.put(colors[1], (x, y))
                    art.put(colors[0], (x, y - 1))
            for x, y in ((4, 8), (27, 25)):
                art.put(colors[0], (x, y))
        skin_images[skin] = [art, art.zoom(2), art.zoom(3), art.zoom(5)]
        for name, index in (("preview", 1), ("cup", 2), ("hero", 3)):
            screen.register_shape(
                skin + "_" + name,
                turtle.Shape("image", skin_images[skin][index]),
            )
    secret = tkinter.PhotoImage(width=32, height=34, master=screen.getcanvas())
    for y in range(34):
        for x in range(32):
            if not image.transparency_get(x, y):
                secret.put("#554b65", (x, y))
    for x, y in (
        (14, 12),
        (15, 12),
        (16, 12),
        (17, 13),
        (17, 14),
        (16, 15),
        (15, 16),
        (15, 19),
    ):
        secret.put("#cbb8c9", (x, y))
    secret_image = secret.zoom(2)
    screen.register_shape("secret_preview", turtle.Shape("image", secret_image))
    spark = turtle.Shape("compound")
    for x, y, w, h, c in (
        (-9, -3, 18, 6, "#b77945"),
        (-6, -6, 12, 12, "#f4bc68"),
        (-3, -9, 6, 18, "#f4bc68"),
        (-3, -3, 6, 6, "#fff1ba"),
    ):
        spark.addcomponent(((x, y), (x + w, y), (x + w, y + h), (x, y + h)), c, c)
    screen.register_shape("spark", spark)
    return {"party": party_images, "skins": skin_images, "secret": secret_image}


def frame(game, x1, y1, x2, y2, fill="#241d30", edge="#715166"):
    r = game.rectangle
    r(x1 + 4, y1 - 4, x2 + 4, y2 - 4, INK)
    r(x1, y1, x2, y2, edge)
    r(x1 + 2, y1 + 2, x2 - 2, y2 - 2, fill)
    for x, y in (
        (x1 + 5, y1 + 5),
        (x2 - 8, y1 + 5),
        (x1 + 5, y2 - 8),
        (x2 - 8, y2 - 8),
    ):
        r(x, y, x + 3, y + 3, "#b08a72")


def guest(game, x, y, shirt, hair="#36263b", scale=3):
    def b(a, c, w, h, color):
        game.rectangle(
            x + a * scale,
            y + c * scale,
            x + (a + w) * scale,
            y + (c + h) * scale,
            color,
        )

    b(3, 20, 10, 3, hair)
    b(2, 16, 12, 5, hair)
    b(4, 13, 8, 6, "#d69b75")
    b(4, 16, 7, 3, "#efba8c")
    b(3, 18, 9, 2, hair)
    b(9, 15, 1, 1, INK)
    b(6, 15, 1, 1, INK)
    b(7, 13, 3, 1, "#ac6e60")
    b(1, 4, 14, 9, INK)
    b(2, 5, 12, 7, shirt)
    b(6, 5, 3, 8, "#eed3ad")
    b(0, 5, 2, 5, shirt)
    b(14, 5, 2, 5, shirt)
    b(0, 3, 2, 2, "#d69b75")
    b(14, 3, 2, 2, "#d69b75")
    b(3, -1, 4, 6, "#353548")
    b(9, -1, 4, 6, "#353548")
    b(2, -2, 5, 2, INK)
    b(9, -2, 5, 2, INK)


def scenery(game, menu=False):
    r = game.rectangle
    left, right = (-470, -35) if menu else (-470, 470)
    game.session.scene_location = (
        "hall" if menu else location(game.session.mode, game.session.level)
    )
    if not menu and location(game.session.mode, game.session.level) != "hall":
        environment(game, location(game.session.mode, game.session.level))
        return
    r(left, -174, right, 236, "#33283f")
    for x in range(left + 12, right - 8, 32):
        for y in range(-65, 220, 36):
            r(x, y, x + 2, y + 4, "#3e304a")
            r(x - 2, y + 2, x + 4, y + 3, "#3e304a")
    r(left, -174, right, -100, "#49303b")
    for y in range(-170, -100, 18):
        r(left, y, right, y + 2, "#322433")
        for x in range(left + 10 + (y % 3) * 15, right - 15, 68):
            r(x, y + 5, min(x + 28, right), y + 6, "#64434b")
    r(left, -99, right, -90, "#b27b58")
    r(left, -98, right, -96, "#d39c6b")
    wx = left + 28
    frame(game, wx, 18, wx + 120, 190, "#222b45", "#976b64")
    r(wx + 8, 26, wx + 112, 182, "#303855")
    for sx, sy in ((18, 152), (85, 133), (39, 104), (97, 167), (20, 75)):
        r(wx + sx, sy, wx + sx + 2, sy + 2, "#a9a4b7")
    r(wx + 70, 142, wx + 90, 164, "#ebce8e")
    r(wx + 73, 139, wx + 87, 167, "#ebce8e")
    r(wx + 82, 151, wx + 94, 171, "#303855")
    for sx, h in ((8, 26), (28, 38), (51, 31), (82, 43)):
        r(wx + sx, 26, wx + sx + 23, 26 + h, "#202238")
    r(wx + 58, 26, wx + 62, 182, "#976b64")
    r(wx + 8, 97, wx + 112, 101, "#976b64")
    for cx in (wx - 6, wx + 106):
        r(cx, 14, cx + 20, 192, "#754354")
        for dx in (3, 9, 15):
            r(cx + dx, 16, cx + dx + 2, 190, "#8b5060")
    r(wx - 10, 192, wx + 134, 198, "#c18e70")
    for i, x in enumerate(range(left + 8, right - 28, 28)):
        y = 222 - (i % 5) * 3
        r(x, y, x + 28, y + 1, "#8c6572")
        r(x + 12, y - 7, x + 14, y, "#9d796f")
        r(x + 10, y - 13, x + 16, y - 7, ("#e1ad70", "#b98196", "#8ba995")[i % 3])
        r(x + 12, y - 10, x + 14, y - 8, "#ffe7ae")
    if menu:
        frame(game, -274, 93, -67, 177, "#292237")
        game.write(game.session.static, -170, 146, "LANTERN HOUSE", 13, "#e7c795")
        game.write(game.session.static, -170, 123, "Est. after sundown", 10, "#b59aaf")
        r(-283, 73, -60, 79, "#ad7959")
        for x, c in ((-260, "#879c8f"), (-244, "#b07988"), (-228, "#d4ae75")):
            r(x, 79, x + 10, 96, c)
            r(x + 2, 81, x + 4, 94, "#e1cba7")
        guest(game, -417, -71, "#829d8c", scale=4)
        guest(game, -132, -71, "#b47b90", hair="#b38361", scale=4)
        r(-445, -108, -55, -85, "#aa7150")
        r(-445, -92, -55, -85, "#d5a071")
        r(-429, -152, -417, -108, "#654238")
        r(-83, -152, -71, -108, "#654238")
        r(-368, -83, -199, -77, "#62433d")
        p = game.session.static
        p.shape("hero_cup")
        p.goto(-281, 5)
        p.stamp()
        game.write(p, -252, -147, "Mira & Theo are saving you a seat.", 10, "#dfc3a8")
    else:
        guest(game, -451, -90, "#829d8c", scale=2)
        guest(game, 419, -90, "#b47b90", hair="#b38361", scale=2)
        r(-456, -148, 456, -82, "#83523e")
        r(-456, -89, 456, -82, "#d4a06c")
        r(-456, -147, 456, -137, "#50333a")
        for x in range(-442, 445, 72):
            r(x, -127, x + 37, -125, "#956448")
            r(x + 9, -109, x + 43, -108, "#956448")


def environment(game, kind):
    """Separate settings, with all scenery kept behind the tracking plane."""
    r = game.rectangle
    wall = {
        "kitchen": "#303c3b",
        "terrace": "#202b43",
        "dawn": "#735761",
        "afterparty": "#241c3c",
    }[kind]
    game.session.scene_location = kind
    r(-470, -174, 470, 236, wall)
    if kind == "kitchen":
        for y in range(40, 175, 22):
            r(-470, y, 470, y + 1, "#41504a")
            for x in range(-458, 460, 36):
                r(x, y, x + 1, y + 22, "#41504a")
        for x in (-447, -379, 330, 398):
            frame(game, x, 79, x + 60, 158, "#657467", "#a8a082")
            r(x + 42, 104, x + 46, 119, "#d1be85")
        r(-448, 60, -315, 66, "#bfa580")
        r(315, 60, 454, 66, "#bfa580")
        for x in (-428, -399, 341, 376, 415):
            r(x, 66, x + 15, 84, "#bc8d6c")
            r(x + 3, 83, x + 12, 90, "#8eab92")
    elif kind in ("terrace", "dawn"):
        if kind == "dawn":
            for y, c in (
                (144, "#ab7471"),
                (116, "#bf8c77"),
                (88, "#d2a386"),
                (60, "#ddbb94"),
            ):
                r(-470, y, 470, y + 28, c)
            r(331, 107, 371, 147, "#ffe6ae")
            r(338, 100, 364, 154, "#ffe6ae")
        else:
            for i in range(55):
                x = -448 + (i * 137) % 880
                y = 65 + (i * 47) % 102
                r(x, y, x + 2, y + 2, "#8f9ab9")
            r(-392, 105, -369, 133, "#ddd1a0")
            r(-385, 99, -376, 139, "#ddd1a0")
            r(-381, 115, -365, 138, wall)
        for i, x in enumerate(range(-470, 470, 48)):
            h = 25 + (i * 17) % 44
            r(x, -40, x + 45, h, "#263142")
            for wy in range(-20, h - 5, 14):
                r(x + 10, wy, x + 13, wy + 4, "#b79879")
        r(-470, -59, 470, -52, "#6a6e79")
        for x in range(-450, 460, 40):
            r(x, -85, x + 4, -52, "#535868")
        for x in (-448, 409):
            r(x, -82, x + 29, -65, "#6d5147")
            for dx, h in ((3, 37), (12, 50), (22, 29)):
                r(x + dx, -65, x + dx + 5, -65 + h, "#6b8977")
    else:
        for x in (-433, 361):
            frame(game, x, -42, x + 72, 145, "#171a2c", "#78639e")
            for y in (4, 86):
                frame(game, x + 10, y - 24, x + 62, y + 24, "#28253d", "#a27abc")
                r(x + 25, y - 10, x + 47, y + 10, "#65548d")
        r(-290, 130, 290, 133, "#cf80be")
        r(-290, 134, 290, 136, "#724f98")
        for x in range(-260, 270, 32):
            h = 10 + ((x + 260) // 32 * 13) % 36
            r(x, 144, x + 14, 144 + h, "#6479a3")
        r(-220, 77, 220, 79, "#436b80")
    guest(game, -451, -90, "#829d8c", scale=2)
    guest(game, 419, -90, "#b47b90", hair="#b38361", scale=2)
    table = "#5e415a" if kind == "afterparty" else "#83523e"
    r(-470, -174, 470, -100, "#302632")
    r(-456, -148, 456, -82, table)
    r(-456, -89, 456, -82, "#d4a06c")
    r(-456, -147, 456, -137, "#50333a")
    for x in range(-442, 445, 72):
        r(x, -127, x + 37, -125, "#956448")


GLYPHS = dict(
    zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        (
            "01110100011000111111100011000110001",
            "11110100011000111110100011000111110",
            "01111100001000010000100001000001111",
            "11110100011000110001100011000111110",
            "11111100001000011110100001000011111",
            "11111100001000011110100001000010000",
            "01111100001000010111100011000101111",
            "10001100011000111111100011000110001",
            "11111001000010000100001000010011111",
            "00111000100001000010100101001001100",
            "10001100101010011000101001001010001",
            "10000100001000010000100001000011111",
            "10001110111010110101100011000110001",
            "10001110011010110011100011000110001",
            "01110100011000110001100011000101110",
            "11110100011000111110100001000010000",
            "01110100011000110001101011001001101",
            "11110100011000111110101001001010001",
            "01111100001000001110000010000111110",
            "11111001000010000100001000010000100",
            "10001100011000110001100011000101110",
            "10001100011000110001100010101000100",
            "10001100011000110101101011101110001",
            "10001100010101000100010101000110001",
            "10001100010101000100001000010000100",
            "11111000010001000100010001000011111",
        ),
    )
)


def pixel_title(game, text, x, y, scale=3, color="#f2bf68"):
    for char in text.upper():
        glyph = GLYPHS.get(char)
        if glyph:
            for row in range(7):
                for col in range(5):
                    if glyph[row * 5 + col] == "1":
                        px = x + col * scale
                        py = y - row * scale
                        game.rectangle(px, py - scale, px + scale, py, color)
        x += 6 * scale
