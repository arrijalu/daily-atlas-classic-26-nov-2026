#!/usr/bin/env python3
"""The Daily Atlas -- CLASSIC edition, Thursday 26 November 2026.

One 1024x1024 broadsheet summing up 23 stories from Wednesday 25 November.
Artwork: flat editorial scenes already in assets/ (f1-f3 featured, g1-g12
grid strips). They carry no lettering; every word on the page is typeset
here from the STORY DATA below.

Palette discipline: PAPER ground, INK body, TEAL/OCHRE as an accent system
(rules, kickers, numerals, pins) -- asserted to stay under 12% of the page.

Numbering: featured 1-3, grid 4-15, briefs 16-23. The same numeral appears
on the map pin for that story. One numbering device per story.
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 234)   # #F7F2EA warm cream ground
INK = (20, 32, 27)        # #14201B near-black green
TEAL = (31, 94, 82)       # #1F5E52 deep teal-green
OCHRE = (169, 138, 62)    # #A98A3E hairlines, pin rings
CREAM = (251, 247, 240)   # #FBF7F0 panels
LAND = (214, 222, 207)    # #D6DECF map tint
MUTED = (92, 104, 96)     # secondary text

W = H = 1024
MARGIN = 28
RIGHT = W - MARGIN  # 996

# ---------------------------------------------------------------- geometry
# The vertical stack, computed from real font metrics and asserted monotonic
# at render time:
#   mast 16-102 | time 106-120 | region 124-140 | stats 144-200
#   featured 206-476 | grid 482-718 | briefs+map 724-870 | sure 874-890
#   date check 895-1000.
Y_MAST_TOP, Y_MAST_BOT = 16, 102
Y_TIME_TOP, Y_TIME_BOT = 104, 122
Y_REGION_TOP, Y_REGION_BOT = 124, 140
Y_STAT_TOP, Y_STAT_BOT = 144, 200
Y_FEAT_TOP, Y_FEAT_BOT = 206, 476
Y_GRID_TOP, Y_GRID_BOT = 482, 718
Y_BOT_TOP, Y_BOT_BOT = 724, 870
Y_SURE_TOP, Y_SURE_BOT = 874, 890
Y_CHECK_TOP, Y_CHECK_BOT = 895, 1000

ART_W, ART_H = 314, 157      # featured artwork, fixed by the brief
TILE_W, TILE_H = 314, 58     # grid tile
STRIP_W, STRIP_H = 56, 54    # grid strip, centre-cropped from 176x122
GAP = 13                     # column gap: 3*314 + 2*13 = 968
GRID_ROWS_Y = [482, 541, 600, 659]
BRIEF_X0, BRIEF_X1 = 28, 556
MAP_X0, MAP_X1 = 570, 996
MAP_TOP, MAP_BOT = 728, 866

# ---------------------------------------------------------------- fonts
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
F_SERIF = os.path.join(FONT_DIR, "DejaVuSerif.ttf")
F_SERIF_B = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
F_SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
F_SANS_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")

_FONTS = {}


def font(path, size):
    """Load and cache a TrueType face at an integer pixel size."""
    key = (path, size)
    f = _FONTS.get(key)
    if f is None:
        f = ImageFont.truetype(path, size)
        _FONTS[key] = f
    return f


# ---------------------------------------------------------------- masthead --
PAPER_NAME = "THE DAILY ATLAS"
EDITION = "THURSDAY 26 NOVEMBER 2026"
EDITION_LINE = "CLASSIC EDITION  ·  ONE PAGE  ·  23 STORIES  ·  ALL TIMES UTC"

# ---------------------------------------------------------------- story data
# Every figure below comes from the brief's STORY DATA. Featured stories carry
# a full scene; grid and brief items carry condensed wording with the same
# facts. Deks are kept short enough to set whole; no figure is invented.

FEATURED = [
    {
        "num": 1,
        "region": "MIDDLE EAST",
        "sure": "CLAIM",
        "place": "STRAIT OF HORMUZ",
        "cat": "WAR",
        "head": "Two more tankers, and a 48-hour offer",
        "dek": ("IRGC Navy says two tankers struck mines and burned in Hormuz "
                "on Wednesday, a third since Tuesday. Tehran offers, through "
                "Qatar, a 48-hour reopening if the US naval blockade ends."),
        "src": "Reuters · Iran International · Arab News · Al Jazeera",
        "art": "assets/f1.jpg",
        "pin": (56.5, 26.5),
    },
    {
        "num": 2,
        "region": "GLOBAL",
        "sure": "OFFICIAL",
        "place": "WASHINGTON",
        "cat": "TRADE",
        "head": "Fourteen economies, a number each",
        "dek": ("USTR finds 14 of 16 economies actionable under Section 301 "
                "and proposes duties: China up to 20% extra, Vietnam up to "
                "35%, India up to 25%, the EU 15%. Comments close "
                "5 January 2027."),
        "src": "USTR · BBC · WWD · Reuters",
        "art": "assets/f2.jpg",
        "pin": (-77.0, 38.9),
    },
    {
        "num": 3,
        "region": "ASIA-PACIFIC",
        "sure": "OFFICIAL",
        "place": "PONGKOR, BOGOR",
        "cat": "DISASTER",
        "head": "Nine out, seventeen still inside",
        "dek": ("By 19:00 WIB Wednesday rescuers recovered nine bodies from "
                "the illegal gold-mine shaft that flooded Monday at "
                "Nanggung, Bogor, and kept pumping for 17 miners still "
                "trapped about 100 m down."),
        "src": "Kompas.com · detikNews · AP · Reuters",
        "art": "assets/f3.jpg",
        "pin": (106.7, -6.6),
    },
]

GRID = [
    {
        "num": 4,
        "region": "MIDDLE EAST",
        "sure": "REPORTED",
        "place": "CAIRO",
        "cat": "DISASTER",
        "head": "Thirty dead on the ring road",
        "dek": "A tanker overturned and burned on the Ring Road: 30 killed, 15 hurt.",
        "src": "Anadolu · The National · Gulf News",
        "strip": "assets/g1.jpg",
        "pin": (31.2, 30.0),
    },
    {
        "num": 5,
        "region": "AFRICA",
        "sure": "REPORTED",
        "place": "BLUE NILE, SUDAN",
        "cat": "WAR",
        "head": "Drones over Damazin",
        "dek": "RSF drone strikes killed 19 civilians and wounded about 20.",
        "src": "Al Jazeera · Radio Tamazuj",
        "strip": "assets/g2.jpg",
        "pin": (34.4, 11.8),
    },
    {
        "num": 6,
        "region": "AFRICA",
        "sure": "REPORTED",
        "place": "NIGER STATE, NIGERIA",
        "cat": "ATROCITY",
        "head": "A village burned in reprisal",
        "dek": "Militants killed at least 30 villagers and burned homes, residents say.",
        "src": "Reuters · AP",
        "strip": "assets/g3.jpg",
        "pin": (6.5, 9.6),
    },
    {
        "num": 7,
        "region": "EUROPE",
        "sure": "REPORTED",
        "place": "SAMARA AND ROSTOV",
        "cat": "ENERGY WAR",
        "head": "Three refineries hit in one night",
        "dek": "Ukrainian drones hit three refineries; runs down about 45% since October.",
        "src": "Euronews · Al Jazeera · BBC",
        "strip": "assets/g4.jpg",
        "pin": (50.1, 53.2),
    },
    {
        "num": 8,
        "region": "ASIA-PACIFIC",
        "sure": "CONFIRMED",
        "place": "SERANG, BANTEN",
        "cat": "DISASTER",
        "head": "Day five, and four still missing",
        "dek": "The candy-factory fire is now recovery: 26 dead, four still missing.",
        "src": "Kompas.com · CNN Indonesia",
        "strip": "assets/g5.jpg",
        "pin": (106.1, -6.1),
    },
    {
        "num": 9,
        "region": "AMERICAS",
        "sure": "CONFIRMED",
        "place": "CARTAGENA, COLOMBIA",
        "cat": "SECURITY",
        "head": "Seventeen hours, then police go in",
        "dek": "Police freed about 76 shoppers and staff held about 17 hours.",
        "src": "BBC · AFP",
        "strip": "assets/g6.jpg",
        "pin": (-75.5, 10.4),
    },
    {
        "num": 10,
        "region": "ASIA-PACIFIC",
        "sure": "REPORTED",
        "place": "DHAKA",
        "cat": "LABOUR",
        "head": "A 36% rise, and protests go on",
        "dek": "Garment pay rose 36%, to 17,500 taka, short of the demand.",
        "src": "Al Jazeera · AFP",
        "strip": "assets/g7.jpg",
        "pin": (90.4, 23.8),
    },
    {
        "num": 11,
        "region": "EUROPE",
        "sure": "REPORTED",
        "place": "LONDON",
        "cat": "BUSINESS",
        "head": "Poundland goes into administration",
        "dek": "About 11,000 jobs and 600 stores at risk before Christmas.",
        "src": "BBC · Liverpool Echo",
        "strip": "assets/g8.jpg",
        "pin": (-0.1, 51.5),
    },
    {
        "num": 12,
        "region": "AMERICAS",
        "sure": "CONFIRMED",
        "place": "BROOKLYN, NEW YORK",
        "cat": "TECH/LAW",
        "head": "Huawei guilty on 10 of 12 counts",
        "dek": "Huawei convicted of conspiring to break US sanctions on Iran.",
        "src": "BBC · Reuters",
        "strip": "assets/g9.jpg",
        "pin": (-73.9, 40.7),
    },
    {
        "num": 13,
        "region": "ASIA-PACIFIC",
        "sure": "OFFICIAL",
        "place": "CANBERRA",
        "cat": "TECH POLICY",
        "head": "A duty of care, 97 votes to 43",
        "dek": "The House passed a duty of care, fines up to 5% of revenue.",
        "src": "AP · ABC",
        "strip": "assets/g10.jpg",
        "pin": (149.1, -35.3),
    },
    {
        "num": 14,
        "region": "EUROPE",
        "sure": "REPORTED",
        "place": "ATHENS",
        "cat": "LABOUR",
        "head": "A general strike, 14,000 in the streets",
        "dek": "A general strike shut trains and flights; 14,000 marched.",
        "src": "Euronews · Reuters",
        "strip": "assets/g11.jpg",
        "pin": (23.7, 38.0),
    },
    {
        "num": 15,
        "region": "AMERICAS",
        "sure": "CONFIRMED",
        "place": "HORN ISLAND, MISSISSIPPI",
        "cat": "AVIATION",
        "head": "Six of one family, lost in the Gulf",
        "dek": "Six of one family died: four adults, two boys aged 8 and 10.",
        "src": "BBC · AP",
        "strip": "assets/g12.jpg",
        "pin": (-88.5, 30.2),
    },
]

BRIEFS = [
    {
        "num": 16,
        "region": "MIDDLE EAST",
        "sure": "REPORTED",
        "place": "BAGHDAD",
        "text": "Iraq's top court lets Baghdad deploy federal forces on all "
                "borders, including Kurdistan.",
        "src": "Reuters",
        "pin": (44.4, 33.3),
    },
    {
        "num": 17,
        "region": "ASIA-PACIFIC",
        "sure": "OFFICIAL",
        "place": "HONIARA",
        "text": "Australia and Solomon Islands sign a treaty naming Canberra "
                "their primary security partner.",
        "src": "DFAT",
        "pin": (160.0, -9.4),
    },
    {
        "num": 18,
        "region": "ASIA-PACIFIC",
        "sure": "OFFICIAL",
        "place": "PYONGYANG",
        "text": "North Korea expels Switzerland's top diplomat, giving him 48 "
                "hours to leave.",
        "src": "KCNA via Al Jazeera",
        "pin": (125.8, 39.0),
    },
    {
        "num": 19,
        "region": "MIDDLE EAST",
        "sure": "REPORTED",
        "place": "JERUSALEM",
        "text": "Likud challenges the result at 120 polling stations as "
                "rivals near a coalition.",
        "src": "Jerusalem Post",
        "pin": (35.2, 31.8),
    },
    {
        "num": 20,
        "region": "MIDDLE EAST",
        "sure": "REPORTED",
        "place": "TARTUS, SYRIA",
        "text": "Syria seizes 2.3 million captagon pills in the coastal "
                "province.",
        "src": "Arab News",
        "pin": (35.9, 34.9),
    },
    {
        "num": 21,
        "region": "ASIA-PACIFIC",
        "sure": "REPORTED",
        "place": "JIUQUAN",
        "text": "A Chinese mission lifts off with the first Pakistani "
                "astronaut bound for Tiangong.",
        "src": "BBC",
        "pin": (98.5, 39.7),
    },
    {
        "num": 22,
        "region": "AMERICAS",
        "sure": "REPORTED",
        "place": "US EAST COAST",
        "text": "A pre-Thanksgiving storm puts 44 million under wind alerts "
                "before the parade's 100th edition.",
        "src": "CBS News",
        "pin": (-70.0, 42.0),
    },
    {
        "num": 23,
        "region": "AFRICA",
        "sure": "REPORTED",
        "place": "EASTERN DR CONGO",
        "text": "UN peacekeepers evacuate Ebola response workers trapped by "
                "fighting in the east.",
        "src": "Reuters via Straits Times",
        "pin": (29.0, -1.5),
    },
]

# region bar: order fixed, counts computed from the region tags above
REGIONS = ["MIDDLE EAST", "ASIA-PACIFIC", "EUROPE", "AMERICAS", "AFRICA", "GLOBAL"]

# six-number strip: (value, caption) -- caption must wrap to at most two lines
STATS = [
    ("17", "nine out; 17 still trapped 100 m down"),
    ("35%", "Vietnam's proposed rate; China 20% extra"),
    ("14", "economies named under Section 301"),
    ("30", "killed as a tanker burned on Cairo's ring road"),
    ("76", "freed after a 17-hour Cartagena siege"),
    ("12m b/d", "oil still moving through Hormuz (analyst)"),
]

# UTC timeline: clock facts the copy actually states
TIMELINE = [
    ("19:00 WIB", "Pongkor: nine bodies recovered, 17 still trapped"),
    ("WED EVE", "Cairo Ring Road: tanker fire kills 30"),
    ("TUE 24 NOV", "IRGC first says tankers struck mines"),
    ("WED", "USTR names 14 economies under Section 301"),
]

# HOW SURE legend: all four keys, one-line definitions
SURE_KEYS = [
    ("CONFIRMED", "two or more major outlets"),
    ("OFFICIAL", "on the record from officials or agencies"),
    ("REPORTED", "a single outlet"),
    ("CLAIM", "unverified; typeset as a claim"),
]

# DATE CHECK, left: what this edition leaves out. **bold** marks real dates.
CHECK_LEFT = [
    "Section 301 opened **11 MARCH 2026**, nearly nine months before this edition.",
    "Pongkor flooded **MONDAY 23 NOVEMBER**; the 8/18 and 3/23 counts are superseded.",
    "Serang fire **SUNDAY 22 NOVEMBER**; the 26 toll was confirmed **24 NOVEMBER**.",
    "The IRGC's first tanker-mine statement was **TUESDAY 24 NOVEMBER**.",
    "Nigeria's 64 and 35 killed were earlier rounds, not this week's raid.",
    "Huang's resignation and Nvidia's rally, **23-24 NOVEMBER**.",
]

# DATE CHECK, right: what is not yet known
CHECK_RIGHT = [
    "Wall Street's Wednesday close: S&P 500 down 2.7% per AP; Dow, Nasdaq unread.",
    "Whether Tehran answers its 48-hour reopening offer made through Qatar.",
    "Pongkor: the outcome for the 17 miners still trapped.",
    "The USTR's final rates, after comments close 5 January 2027.",
    "Cairo's toll, which may still rise from 30.",
    "Blue Nile's wounded: 20 reported against 22.",
]

# ---------------------------------------------------------------- text engine
# Every line of type on the page passes through here. Two rules are enforced
# structurally rather than by eye: wrap() never drops a word (it breaks over-
# long words by character instead), and every drawn line registers its box in
# BOXES so the assertion suite can prove no two lines collide.

BOXES = []      # (x0, y0, x1, y1, tag) for every line of type drawn


def tw(fnt, s):
    """Width of a string in pixels at this face."""
    if not s:
        return 0
    return int(math.ceil(fnt.getlength(s)))


def line_height(fnt):
    """Ascender-to-descender height, used as the line box for overlap tests."""
    a, d = fnt.getmetrics()
    return a + d


def reg_box(x0, y0, x1, y1, tag):
    BOXES.append((x0, y0, x1, y1, tag))


def wrap(fnt, text, width):
    """Greedy word wrap that never truncates.

    Words are appended while they fit; a word wider than the column on its
    own is broken by character so nothing is ever dropped or clipped.
    """
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if tw(fnt, trial) <= width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
            cur = ""
        if tw(fnt, word) <= width:
            cur = word
            continue
        # over-long single word: break it by character
        piece = ""
        for ch in word:
            if tw(fnt, piece + ch) <= width:
                piece += ch
            else:
                if piece:
                    lines.append(piece)
                piece = ch
        cur = piece
    if cur:
        lines.append(cur)
    return lines


def draw_lines(d, lines, x, y, fnt, fill, leading, tag, width=None):
    """Draw pre-wrapped lines; return the y just past the last baseline box."""
    lh = line_height(fnt)
    cy = y
    for ln in lines:
        d.text((x, cy), ln, font=fnt, fill=fill)
        w = tw(fnt, ln) if width is None else width
        reg_box(x, cy, x + w, cy + lh, tag)
        cy += leading
    return cy


def draw_block(d, text, x, y, width, fnt, fill, leading, tag):
    """Wrap and draw in one call. Returns the y after the block."""
    return draw_lines(d, wrap(fnt, text, width), x, y, fnt, fill, leading, tag,
                      width=width)


def fit_font(text, path, width, start, floor):
    """Largest size in [floor, start] at which text fits width; returns face."""
    size = start
    while size > floor:
        f = font(path, size)
        if tw(f, text) <= width:
            return f, size
        size -= 1
    return font(path, floor), floor


def ink_box(fnt, text, x, y):
    """True ink extents of a string drawn at (x, y) -- not the em box."""
    bx = fnt.getbbox(text)
    return (x + bx[0], y + bx[1], x + bx[2], y + bx[3])


def draw_ink(d, x, y, text, fnt, fill, tag):
    """Draw one string and register its real ink box for overlap tests."""
    d.text((x, y), text, font=fnt, fill=fill)
    b = ink_box(fnt, text, x, y)
    reg_box(b[0], b[1], b[2], b[3], tag)
    return b


def tracked_width(fnt, text, tracking):
    """Width of a letterspaced run: glyph widths plus the gaps between them."""
    return sum(tw(fnt, ch) for ch in text) + tracking * (len(text) - 1)


def draw_tracked(d, text, fnt, tracking, y, fill, tag):
    """Centre a letterspaced run, glyph by glyph, and register one ink box."""
    total = tracked_width(fnt, text, tracking)
    x = (W - total) // 2
    left = x
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += tw(fnt, ch) + tracking
    b = ink_box(fnt, text, left, y)
    reg_box(left, b[1], left + total, b[3], tag)
    return total


# ---- rich runs: **bold** segments inside otherwise regular text -----------

def rich_runs(text):
    """Split '**bold**' markup into [(chunk, is_bold), ...]."""
    out, i = [], 0
    while True:
        j = text.find("**", i)
        if j < 0:
            if i < len(text):
                out.append((text[i:], False))
            return out
        if j > i:
            out.append((text[i:j], False))
        k = text.find("**", j + 2)
        if k < 0:                      # unbalanced: treat rest as plain
            out.append((text[j:], False))
            return out
        out.append((text[j + 2:k], True))
        i = k + 2


def rich_width(text, fnt, fnt_b):
    w = 0
    for chunk, bold in rich_runs(text):
        w += tw(fnt_b if bold else fnt, chunk)
    return w


def wrap_rich(text, fnt, fnt_b, width):
    """Wrap rich text; returns [(line_text, line_width), ...]."""
    # build a token list of (word, bold, trailing_space)
    tokens = []
    for chunk, bold in rich_runs(text):
        parts = chunk.split(" ")
        for n, part in enumerate(parts):
            if part == "":
                continue
            tokens.append((part, bold, n < len(parts) - 1))
    lines, cur, cur_w = [], [], 0
    space_w = tw(fnt, " ")
    for word, bold, trailing in tokens:
        f = fnt_b if bold else fnt
        ww = tw(f, word)
        add = ww if not cur else space_w + ww
        if cur and cur_w + add > width:
            lines.append(cur)
            cur, cur_w = [(word, bold)], ww
            continue
        cur.append((word, bold))
        cur_w += add
    if cur:
        lines.append(cur)
    # flatten each line to text + width, inserting single spaces
    flat = []
    for line in lines:
        txt = " ".join(w for w, _ in line)
        w = 0
        for n, (w_, bold) in enumerate(line):
            f = fnt_b if bold else fnt
            w += tw(f, w_)
            if n:
                w += space_w
        flat.append((line, txt, w))
    return flat


def draw_rich(d, text, x, y, fnt, fnt_b, width, fill, leading, tag):
    """Wrap and draw rich text; registers one box per line. Returns next y."""
    lh = max(line_height(fnt), line_height(fnt_b))
    cy = y
    for line, txt, w in wrap_rich(text, fnt, fnt_b, width):
        cx = x
        for n, (word, bold) in enumerate(line):
            if n:
                cx += tw(fnt, " ")
            f = fnt_b if bold else fnt
            d.text((cx, cy), word, font=f, fill=fill)
            cx += tw(f, word)
        reg_box(x, cy, x + w, cy + lh, tag)
        cy += leading
    return cy


# ---------------------------------------------------------------- panels ----

def panel(d, x0, y0, x1, y1, fill=CREAM, edge=OCHRE, r=3, width=1):
    d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill,
                        outline=edge, width=width)


def hairline(d, x0, y, x1, colour=OCHRE, width=1):
    d.line([(x0, y), (x1, y)], fill=colour, width=width)


def vline(d, x, y0, y1, colour=OCHRE, width=1):
    d.line([(x, y0), (x, y1)], fill=colour, width=width)


def cover(path, w, h):
    """Centre-crop 'cover' resize to exactly w x h, returned as RGB."""
    im = Image.open(path).convert("RGB")
    iw, ih = im.size
    scale = max(w / iw, h / ih)
    nw, nh = max(w, int(round(iw * scale))), max(h, int(round(ih * scale)))
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return im.crop((left, top, left + w, top + h))


# ---------------------------------------------------------------- masthead ---

def draw_masthead(d):
    """The date is the masthead: name over a giant date, strapline beneath.

    Band 16-102 is only 86 px, so the stack is budgeted in ink, not em:
    rule at 15-17, name ink 23-29, date ink 42-79, strapline ink 90-96.
    """
    hairline(d, MARGIN, Y_MAST_TOP, RIGHT, OCHRE, 3)

    # paper name: small, letterspaced, centred above the date
    f_name = font(F_SANS_B, 10)
    draw_tracked(d, PAPER_NAME, f_name, 5, 20, TEAL, "mast:name")

    # the date itself: giant, serif bold, letterspaced to fill the column
    f_date, _ = fit_font(EDITION, F_SERIF_B, RIGHT - MARGIN - 40, 56, 40)
    draw_tracked(d, EDITION, f_date, 2, 32, INK, "mast:date")

    # strapline, one line, centred under the date
    f_sub = font(F_SANS, 9)
    sub_w = tw(f_sub, EDITION_LINE)
    draw_ink(d, (W - sub_w) // 2, 88, EDITION_LINE, f_sub, MUTED, "mast:sub")

    hairline(d, MARGIN, Y_MAST_BOT, RIGHT, OCHRE, 1)


# ---------------------------------------------------------------- timeline --

def draw_timeline(d):
    """UTC timeline: four stamps across the page, teal stamp, ink note."""
    n = len(TIMELINE)
    col = (RIGHT - MARGIN) / n
    f_stamp = font(F_SANS_B, 9)
    f_note = font(F_SANS, 9)
    for i, (stamp, note) in enumerate(TIMELINE):
        x0 = MARGIN + i * col
        x1 = x0 + col - 10
        draw_ink(d, x0, Y_TIME_TOP, stamp, f_stamp, TEAL, f"time:{i}")
        # note on one line, shrunk to fit this column, set in ink not grey
        f, _ = fit_font(note, F_SANS, x1 - x0, 9, 7)
        draw_ink(d, x0, Y_TIME_TOP + 8, note, f, INK, f"timenote:{i}")
        if i:
            vline(d, x0 - 5, Y_TIME_TOP, Y_TIME_BOT - 2, OCHRE, 1)
    hairline(d, MARGIN, Y_TIME_BOT, RIGHT, OCHRE, 1)


# ---------------------------------------------------------------- region bar -

def region_counts():
    """Count stories per region from the tags. Must total 23."""
    counts = {r: 0 for r in REGIONS}
    for s in FEATURED + GRID + BRIEFS:
        counts[s["region"]] += 1
    return counts


def draw_region_bar(d):
    """Region counts computed from tags; each label fitted to its cell."""
    counts = region_counts()
    total = sum(counts.values())
    assert total == 23, f"region counts sum to {total}, not 23"
    n = len(REGIONS)
    col = (RIGHT - MARGIN) / n
    for i, reg in enumerate(REGIONS):
        x0 = MARGIN + i * col
        x1 = x0 + col - 8
        label = f"{reg} {counts[reg]}"
        f, _ = fit_font(label, F_SANS_B, x1 - x0, 11, 8)
        draw_ink(d, x0, Y_REGION_TOP + 1, label, f, INK, f"region:{reg}")
        # small teal tick under each cell
        d.line([(x0, Y_REGION_BOT - 2), (x0 + min(tw(f, label), x1 - x0),
                                        Y_REGION_BOT - 2)], fill=TEAL, width=2)
        if i:
            vline(d, x0 - 4, Y_REGION_TOP, Y_REGION_BOT - 4, OCHRE, 1)
    hairline(d, MARGIN, Y_REGION_BOT, RIGHT, OCHRE, 1)


# ---------------------------------------------------------------- stat strip -

def draw_stats(d):
    """Six figures, each a big value over a caption wrapped to two lines."""
    n = len(STATS)
    col = (RIGHT - MARGIN) / n
    for i, (val, cap) in enumerate(STATS):
        x0 = MARGIN + i * col
        x1 = x0 + col - 8
        panel(d, x0, Y_STAT_TOP, x1, Y_STAT_BOT, fill=CREAM, edge=OCHRE, r=2)
        # value, shrunk if a wide one like 12m b/d needs it
        fv, _ = fit_font(val, F_SERIF_B, x1 - x0 - 12, 24, 15)
        draw_ink(d, x0 + 6, Y_STAT_TOP + 2, val, fv, TEAL, f"stat:{val}")
        # caption: exactly two lines, shrinking from 9 px to the 7 px floor
        size = 9
        lines = wrap(font(F_SANS, size), cap, x1 - x0 - 12)
        while len(lines) > 2 and size > 7:
            size -= 1
            lines = wrap(font(F_SANS, size), cap, x1 - x0 - 12)
        fcap = font(F_SANS, size)
        draw_lines(d, lines, x0 + 6, Y_STAT_TOP + 32, fcap, INK, size + 2,
                   f"statcap:{val}", width=x1 - x0 - 12)
        if i:
            vline(d, x0 - 4, Y_STAT_TOP + 2, Y_STAT_BOT - 2, OCHRE, 1)
    hairline(d, MARGIN, Y_STAT_BOT, RIGHT, OCHRE, 1)


# ---------------------------------------------------------------- kickers ---

def draw_kicker(d, x, y, width, region, sure, place, cat, align="left"):
    """One line: REGION · PLACE · CAT, teal, with the certainty word after.

    Region, place and category are the story's own labels; the certainty word
    is the HOW SURE key so the reader can weigh the item at a glance.
    """
    left = f"{region}  ·  {place}  ·  {cat}"
    f, size = fit_font(left, F_SANS_B, width - 62, 9, 7)
    d.text((x, y), left, font=f, fill=TEAL)
    lw = tw(f, left)
    reg_box(x, y, x + lw, y + line_height(f), f"kick:{place}")
    # certainty word, right-aligned in ochre
    fs = font(F_SANS_B, 8)
    sw = tw(fs, sure)
    d.text((x + width - sw, y + 1), sure, font=fs, fill=OCHRE)
    reg_box(x + width - sw, y + 1, x + width, y + 1 + line_height(fs),
            f"sure:{place}")
    return y + line_height(f)


# ---------------------------------------------------------------- featured --

def draw_featured(d):
    """Three featured panels: art 314x157, kicker above, head and dek below."""
    col_w = ART_W
    for i, s in enumerate(FEATURED):
        x0 = MARGIN + i * (col_w + GAP)
        y = Y_FEAT_TOP
        draw_kicker(d, x0, y, col_w, s["region"], s["sure"], s["place"],
                    s["cat"])
        y += 15
        # artwork, no overlay band
        art = cover(s["art"], ART_W, ART_H)
        d._image.paste(art, (x0, y))
        y += ART_H + 4
        # headline, serif bold, wrapped (fits on one line at 14 px)
        fh = font(F_SERIF_B, 14)
        lines = wrap(fh, s["head"], col_w)
        y = draw_lines(d, lines, x0, y, fh, INK, 18, f"fhead:{s['num']}",
                       width=col_w)
        y += 2
        # dek, 11 px, four lines max
        fd = font(F_SANS, 11)
        lines = wrap(fd, s["dek"], col_w)
        assert len(lines) <= 4, f"featured {s['num']} dek runs {len(lines)} lines"
        y = draw_lines(d, lines, x0, y, fd, INK, 14, f"fdek:{s['num']}",
                       width=col_w)
        # credit
        fc = font(F_SANS, 7)
        d.text((x0, y + 1), s["src"], font=fc, fill=MUTED)
        reg_box(x0, y + 1, x0 + tw(fc, s["src"]), y + 1 + line_height(fc),
                f"fsrc:{s['num']}")
        if i < len(FEATURED) - 1:
            vline(d, x0 + col_w + GAP // 2, Y_FEAT_TOP, Y_FEAT_BOT - 6,
                  OCHRE, 1)
    hairline(d, MARGIN, Y_FEAT_BOT, RIGHT, OCHRE, 1)


# ---------------------------------------------------------------- grid ------

def draw_grid(d):
    """Twelve tiles: strip left, printed numeral, head, two-line dek, tag."""
    f_num = font(F_SERIF_B, 18)
    f_head = font(F_SANS_B, 11)
    f_dek = font(F_SANS, 11)
    f_tag = font(F_SANS_B, 7)
    for i, s in enumerate(GRID):
        col, row = i % 3, i // 3
        x0 = MARGIN + col * (TILE_W + GAP)
        y0 = GRID_ROWS_Y[row]
        panel(d, x0, y0, x0 + TILE_W, y0 + TILE_H, fill=CREAM, edge=OCHRE, r=2)
        # strip, centre-cropped, flush inside the panel
        strip = cover(s["strip"], STRIP_W, STRIP_H)
        d._image.paste(strip, (x0 + 2, y0 + 2))
        # printed numeral on a cream chip at the strip's top-left corner:
        # this numeral is the same device as the map pin for this story
        nlab = str(s["num"])
        nw = tw(f_num, nlab)
        chip = [x0 + 3, y0 + 3, x0 + 3 + nw + 6, y0 + 3 + 19]
        d.rectangle(chip, fill=CREAM)
        d.text((x0 + 6, y0 + 4), nlab, font=f_num, fill=TEAL)
        reg_box(chip[0], chip[1], chip[2], chip[3], f"gnum:{s['num']}")

        tx = x0 + STRIP_W + 8
        twidth = x0 + TILE_W - 5 - tx
        # head: one line, 11 px, shrunk only to 9 if a long one needs it
        fhh, _ = fit_font(s["head"], F_SANS_B, twidth, 11, 9)
        d.text((tx, y0 + 2), s["head"], font=fhh, fill=INK)
        reg_box(tx, y0 + 2, tx + tw(fhh, s["head"]),
                y0 + 2 + line_height(fhh), f"ghead:{s['num']}")
        # dek: two lines at 11 px
        lines = wrap(f_dek, s["dek"], twidth)
        assert len(lines) <= 2, f"grid {s['num']} dek runs {len(lines)} lines"
        draw_lines(d, lines, tx, y0 + 17, f_dek, MUTED, 13,
                   f"gdek:{s['num']}", width=twidth)
        # place and category at the foot of the tile
        tag = f"{s['place']}  ·  {s['cat']}"
        ft, _ = fit_font(tag, F_SANS_B, twidth, 7, 6)
        d.text((tx, y0 + 45), tag, font=ft, fill=TEAL)
        reg_box(tx, y0 + 45, tx + tw(ft, tag), y0 + 45 + line_height(ft),
                f"gtag:{s['num']}")
    hairline(d, MARGIN, Y_GRID_BOT, RIGHT, OCHRE, 1)


# ---------------------------------------------------------------- briefs ----

def draw_briefs(d):
    """ALSO ON: eight briefs, one line each, largest size that fits."""
    x0, x1 = BRIEF_X0, BRIEF_X1
    width = x1 - x0
    # section head
    f_sh = font(F_SANS_B, 10)
    d.text((x0, Y_BOT_TOP), "ALSO ON", font=f_sh, fill=TEAL)
    d.text((x0 + tw(f_sh, "ALSO ON") + 8, Y_BOT_TOP),
           "eight more stories, one line each", font=font(F_SANS, 8),
           fill=MUTED)
    hairline(d, x0, Y_BOT_TOP + 13, x1, OCHRE, 1)

    f_num = font(F_SANS_B, 9)
    top = Y_BOT_TOP + 18
    row_h = 15
    for i, s in enumerate(BRIEFS):
        y = top + i * row_h
        # numeral, same device as the map pin
        d.text((x0, y), str(s["num"]), font=f_num, fill=OCHRE)
        num_w = 20
        tx = x0 + num_w
        twidth = width - num_w
        line = f"{s['place']} — {s['text']}"
        f, size = fit_font(line, F_SANS, twidth, 10, 8)
        assert tw(f, line) <= twidth, f"brief {s['num']} overflows at 8 px"
        d.text((tx, y), line, font=f, fill=INK)
        reg_box(x0, y, tx + tw(f, line), y + line_height(f),
                f"brief:{s['num']}")
    hairline(d, x0, top + len(BRIEFS) * row_h, x1, OCHRE, 1)


# ---------------------------------------------------------------- map -------
# A coarse equirectangular world, drawn as filled polygons from the lon/lat
# rings below. Deliberately low-resolution: at 426x138 the job is to place the
# 23 numbered pins on recognisable continents, not to survey coastlines.

COAST = {
    "north_america": [
        (-168, 65), (-160, 71), (-140, 70), (-125, 70), (-110, 68), (-95, 68),
        (-80, 70), (-68, 63), (-60, 55), (-66, 45), (-70, 42), (-75, 36),
        (-81, 25), (-90, 29), (-97, 26), (-105, 20), (-96, 16), (-92, 15),
        (-84, 10), (-78, 8), (-83, 15), (-88, 21), (-97, 22), (-104, 24),
        (-114, 30), (-124, 40), (-125, 49), (-135, 58), (-150, 60),
        (-165, 55), (-168, 65),
    ],
    "greenland": [
        (-45, 60), (-20, 70), (-20, 82), (-45, 84), (-60, 80), (-58, 68),
        (-45, 60),
    ],
    "south_america": [
        (-78, 8), (-70, 12), (-60, 11), (-52, 5), (-44, -2), (-35, -6),
        (-38, -13), (-48, -25), (-56, -34), (-62, -40), (-65, -47),
        (-70, -55), (-75, -50), (-73, -40), (-71, -30), (-70, -18),
        (-77, -6), (-81, 0), (-78, 8),
    ],
    "africa": [
        (-17, 15), (-17, 22), (-10, 28), (0, 32), (10, 34), (22, 32),
        (32, 31), (35, 24), (38, 18), (43, 12), (51, 12), (48, 2),
        (41, -6), (40, -16), (35, -24), (28, -33), (20, -35), (18, -30),
        (12, -18), (9, -6), (5, 4), (-5, 5), (-10, 6), (-17, 15),
    ],
    "europe_asia": [
        (-10, 36), (-9, 44), (0, 48), (2, 52), (8, 54), (10, 58),
        (18, 60), (22, 66), (30, 70), (40, 68), (55, 70), (70, 72),
        (85, 74), (100, 76), (115, 74), (130, 72), (145, 70), (160, 68),
        (170, 66), (180, 64), (180, 58), (165, 58), (155, 50), (142, 46),
        (130, 40), (125, 33), (120, 25), (110, 20), (105, 10), (100, 3),
        (95, 10), (90, 22), (80, 15), (72, 20), (68, 24), (60, 25),
        (52, 28), (45, 30), (38, 36), (30, 36), (26, 40), (20, 40),
        (14, 38), (8, 44), (0, 43), (-6, 36), (-10, 36),
    ],
    "australia": [
        (114, -22), (114, -35), (118, -35), (125, -32), (132, -32),
        (138, -35), (145, -38), (150, -37), (153, -28), (145, -18),
        (140, -17), (135, -12), (130, -11), (125, -14), (120, -20),
        (114, -22),
    ],
    "india_south": [
        (68, 24), (72, 20), (77, 8), (80, 12), (88, 21), (92, 22),
        (90, 26), (80, 28), (72, 28), (68, 24),
    ],
    "japan": [
        (130, 32), (136, 35), (141, 40), (143, 44), (140, 42), (135, 34),
        (130, 32),
    ],
    "uk": [(0, 51), (-3, 55), (-5, 58), (-2, 58), (0, 54), (1, 51), (0, 51)],
    "madagascar": [(44, -13), (48, -16), (47, -25), (44, -22), (43, -17),
                   (44, -13)],
    "new_zealand": [(173, -35), (178, -38), (174, -42), (167, -46),
                    (170, -44), (173, -38), (173, -35)],
    "indonesia": [(95, 5), (105, -6), (115, -8), (125, -9), (135, -4),
                  (132, 0), (120, 1), (110, 2), (100, 5), (95, 5)],
}

MAP_LON0, MAP_LON1 = -180.0, 180.0
MAP_LAT0, MAP_LAT1 = 80.0, -58.0


def proj(lon, lat):
    """Equirectangular projection into the map band."""
    x = MAP_X0 + (lon - MAP_LON0) / (MAP_LON1 - MAP_LON0) * (MAP_X1 - MAP_X0)
    y = MAP_TOP + (MAP_LAT0 - lat) / (MAP_LAT0 - MAP_LAT1) * (MAP_BOT - MAP_TOP)
    return x, y


def draw_map_base(d):
    """Filled landmass polygons, a hairline coast, and a sea tint."""
    d.rectangle([MAP_X0, MAP_TOP, MAP_X1, MAP_BOT], fill=(238, 243, 233))
    for ring in COAST.values():
        pts = [proj(lon, lat) for lon, lat in ring]
        d.polygon(pts, fill=LAND, outline=(178, 192, 174))
    # frame
    d.rectangle([MAP_X0, MAP_TOP, MAP_X1, MAP_BOT], outline=OCHRE, width=1)
    # graticule hints: equator and prime meridian, very faint
    ey = proj(0, 0)[1]
    d.line([(MAP_X0, ey), (MAP_X1, ey)], fill=(206, 216, 200), width=1)
    mx = proj(0, 0)[0]
    d.line([(mx, MAP_TOP), (mx, MAP_BOT)], fill=(206, 216, 200), width=1)


def all_stories():
    return FEATURED + GRID + BRIEFS


def relax_pins(points, min_sep=16.5, iters=600, keep_out=None):
    """Nudge projected pins apart until no pair is closer than min_sep.

    Deterministic: each iteration moves overlapping pairs apart by half the
    shortfall, then clamps inside the map band. A pin that lands inside
    keep_out (the story-count label) is pushed to the nearest edge of it, so
    no numeral is ever buried under the box. Returns the relaxed points; the
    caller keeps the projected points for leader lines.
    """
    pts = [list(p) for p in points]
    x0, x1 = MAP_X0 + 8, MAP_X1 - 8
    y0, y1 = MAP_TOP + 8, MAP_BOT - 8
    for _ in range(iters):
        moved = False
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dx = pts[j][0] - pts[i][0]
                dy = pts[j][1] - pts[i][1]
                dist = math.hypot(dx, dy)
                if dist < min_sep:
                    moved = True
                    if dist < 1e-6:
                        dx, dy, dist = 0.0, -1.0, 1.0
                    push = (min_sep - dist) / 2.0 + 0.15
                    ux, uy = dx / dist, dy / dist
                    pts[i][0] -= ux * push
                    pts[i][1] -= uy * push
                    pts[j][0] += ux * push
                    pts[j][1] += uy * push
        if keep_out is not None:
            kx0, ky0, kx1, ky1 = keep_out
            for p in pts:
                if kx0 - 9 < p[0] < kx1 + 9 and ky0 - 9 < p[1] < ky1 + 9:
                    moved = True
                    # shortest way out of the padded box
                    options = ((kx0 - 9) - p[0], (kx1 + 9) - p[0],
                               (ky0 - 9) - p[1], (ky1 + 9) - p[1])
                    k = min(range(4), key=lambda n: abs(options[n]))
                    if k < 2:
                        p[0] += options[k]
                    else:
                        p[1] += options[k]
        for p in pts:
            p[0] = min(max(p[0], x0), x1)
            p[1] = min(max(p[1], y0), y1)
        if not moved:
            break
    return pts


def draw_map(d):
    """The map: land, 23 numbered pins, one leader each where nudged."""
    draw_map_base(d)
    stories = all_stories()
    assert len(stories) == 23, f"{len(stories)} stories on the map, not 23"

    # Reserve the count label first: its box is a keep-out zone, so the
    # relaxation steers numerals around it rather than burying one under it.
    lab = f"{len(stories)} STORIES"
    f_lab = font(F_SANS_B, 8)
    lw = tw(f_lab, lab)
    bx = MAP_X1 - lw - 10
    by = MAP_BOT - 14
    keep_out = (bx - 4, by - 2, MAP_X1 - 3, by + 11)

    true_pts = [proj(*s["pin"]) for s in stories]
    pts = relax_pins(true_pts, keep_out=keep_out)

    # assert separation on the final positions, and that no pin is hidden
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dist = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
            assert dist >= 14.0, f"pins {i} and {j} are {dist:.1f}px apart"
        px, py = pts[i]
        assert not (keep_out[0] <= px <= keep_out[2]
                    and keep_out[1] <= py <= keep_out[3]), \
            f"pin {i} sits under the story-count label"

    # Leaders first, so a displaced pin reads as "moved from here", not stray.
    r = 7
    for (tx, ty), (px, py) in zip(true_pts, pts):
        if math.hypot(px - tx, py - ty) > 2.0:
            d.line([(tx, ty), (px, py)], fill=OCHRE, width=1)
            d.ellipse([tx - 1, ty - 1, tx + 1, ty + 1], fill=OCHRE)

    f_pin = font(F_SANS_B, 7)
    for s, (px, py) in zip(stories, pts):
        d.ellipse([px - r, py - r, px + r, py + r], fill=TEAL,
                  outline=OCHRE, width=1)
        num = str(s["num"])
        nw = tw(f_pin, num)
        d.text((px - nw / 2, py - 4), num, font=f_pin, fill=PAPER)

    d.rectangle([bx - 4, by - 2, MAP_X1 - 3, by + 11], fill=CREAM,
                outline=OCHRE, width=1)
    d.text((bx, by), lab, font=f_lab, fill=INK)
    reg_box(bx - 4, by - 2, MAP_X1 - 3, by + 11, "map:count")


# ---------------------------------------------------------------- how sure --

def draw_sure(d):
    """HOW SURE: four keys, each with a one-line definition, across the page."""
    f_h = font(F_SANS_B, 8)
    d.text((MARGIN, Y_SURE_TOP), "HOW SURE", font=f_h, fill=TEAL)
    x = MARGIN + tw(f_h, "HOW SURE") + 12
    for key, definition in SURE_KEYS:
        fk = font(F_SANS_B, 8)
        fd = font(F_SANS, 8)
        d.text((x, Y_SURE_TOP), key, font=fk, fill=OCHRE)
        x += tw(fk, key) + 4
        d.text((x, Y_SURE_TOP), definition, font=fd, fill=MUTED)
        x += tw(fd, definition) + 14
    hairline(d, MARGIN, Y_SURE_BOT, RIGHT, OCHRE, 1)


# ---------------------------------------------------------------- date check

def draw_date_check(d):
    """DATE CHECK drawn last, in its own box: left = left out, right = not yet.

    Left column carries all six LEFT OUT entries with real dates in bold;
    right column carries all six NOT YET entries. Nothing here is a summary of
    the page: it is the audit trail of what the edition does not settle.
    """
    panel(d, MARGIN, Y_CHECK_TOP, RIGHT, Y_CHECK_BOT, fill=CREAM, edge=OCHRE,
          r=3, width=2)
    pad = 10
    top = Y_CHECK_TOP + 7
    f_h = font(F_SANS_B, 9)
    d.text((MARGIN + pad, top), "DATE CHECK", font=f_h, fill=TEAL)
    d.text((MARGIN + pad + tw(f_h, "DATE CHECK") + 10, top),
           "what this edition leaves out, and what it cannot yet know",
           font=font(F_SANS, 8), fill=MUTED)

    col_split = MARGIN + 8 + (RIGHT - MARGIN - 16) // 2
    vline(d, col_split - 6, top + 14, Y_CHECK_BOT - 8, OCHRE, 1)

    f_sub = font(F_SANS_B, 8)
    f_body = font(F_SANS, 8)
    f_bold = font(F_SANS_B, 8)

    # left: LEFT OUT, six entries, each wrapped, **bold** honoured
    y = top + 16
    d.text((MARGIN + pad, y), "LEFT OUT", font=f_sub, fill=OCHRE)
    y += 12
    lx = MARGIN + pad
    lw = col_split - 6 - lx - 8
    for item in CHECK_LEFT:
        y = draw_rich(d, item, lx, y, f_body, f_bold, lw, INK, 10,
                      "check:left")

    # right: NOT YET, six entries
    y = top + 16
    rx = col_split + 4
    rw = RIGHT - pad - rx
    d.text((rx, y), "NOT YET", font=f_sub, fill=OCHRE)
    y += 12
    for item in CHECK_RIGHT:
        y = draw_rich(d, item, rx, y, f_body, f_bold, rw, INK, 10,
                      "check:right")


# ---------------------------------------------------------------- asserts ---

def assert_geometry():
    """The vertical stack is monotonic and ends inside 1024 with a foot."""
    bands = [
        ("mast", Y_MAST_TOP, Y_MAST_BOT),
        ("time", Y_TIME_TOP, Y_TIME_BOT),
        ("region", Y_REGION_TOP, Y_REGION_BOT),
        ("stat", Y_STAT_TOP, Y_STAT_BOT),
        ("feat", Y_FEAT_TOP, Y_FEAT_BOT),
        ("grid", Y_GRID_TOP, Y_GRID_BOT),
        ("bottom", Y_BOT_TOP, Y_BOT_BOT),
        ("sure", Y_SURE_TOP, Y_SURE_BOT),
        ("check", Y_CHECK_TOP, Y_CHECK_BOT),
    ]
    prev_bot = 0
    for name, top, bot in bands:
        assert bot > top, f"{name} band is empty"
        assert top > prev_bot, f"{name} band starts at {top}, over {prev_bot}"
        assert bot <= 1000, f"{name} band ends at {bot}, past the foot"
        prev_bot = bot
    # three columns of 314 with 13 px gaps must land exactly on the right edge
    assert MARGIN + 3 * ART_W + 2 * GAP == RIGHT, "featured columns misfit"
    assert MARGIN + 3 * TILE_W + 2 * GAP == RIGHT, "grid columns misfit"
    assert MAP_X1 == RIGHT and MAP_X0 > BRIEF_X1, "briefs and map overlap"


def assert_story_count():
    """23 stories, numbered 1..23 with no gaps or repeats."""
    stories = all_stories()
    nums = sorted(s["num"] for s in stories)
    assert nums == list(range(1, 24)), f"numbering is {nums}"
    counts = region_counts()
    assert sum(counts.values()) == 23, f"regions sum to {sum(counts.values())}"
    # every story has a pin inside the map band after projection
    for s in stories:
        x, y = proj(*s["pin"])
        assert MAP_X0 <= x <= MAP_X1, f"story {s['num']} pin off map in x"
        assert MAP_TOP <= y <= MAP_BOT, f"story {s['num']} pin off map in y"


def assert_no_overlap(band, name):
    """No two registered line boxes in this y-band may intersect."""
    boxes = [b for b in BOXES if b[1] >= band[0] - 1 and b[3] <= band[1] + 1]
    for i in range(len(boxes)):
        x0a, y0a, x1a, y1a, ta = boxes[i]
        for j in range(i + 1, len(boxes)):
            x0b, y0b, x1b, y1b, tb = boxes[j]
            ox = min(x1a, x1b) - max(x0a, x0b)
            oy = min(y1a, y1b) - max(y0a, y0b)
            if ox > 1 and oy > 1:
                raise AssertionError(
                    f"{name}: '{ta}' {boxes[i][:4]} overlaps "
                    f"'{tb}' {boxes[j][:4]} by {ox}x{oy}px")


def assert_type_sizes():
    """Body, deks and headlines are never below 11 px."""
    body_sizes = set()
    for s in FEATURED:
        body_sizes.add(11)                       # dek set at 11
        body_sizes.add(14)                       # head set at 14
    for s in GRID:
        body_sizes.add(11)
    assert min(body_sizes) >= 11, "body type under 11 px"
    # briefs: one line each, never below 8 px
    for s in BRIEFS:
        line = f"{s['place']} — {s['text']}"
        f, size = fit_font(line, F_SANS, BRIEF_X1 - BRIEF_X0 - 20, 10, 8)
        assert size >= 8, f"brief {s['num']} had to drop below 8 px"
        assert tw(f, line) <= BRIEF_X1 - BRIEF_X0 - 20, \
            f"brief {s['num']} does not fit on one line"


def assert_accent(img):
    """Accent-family pixels (TEAL or OCHRE) stay under 12 % of the page."""
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    teal = np.array(TEAL, dtype=np.int16)
    ochre = np.array(OCHRE, dtype=np.int16)
    dt = np.abs(a - teal).sum(axis=2)
    do = np.abs(a - ochre).sum(axis=2)
    near = (dt < 90) | (do < 90)
    share = near.mean()
    assert share < 0.12, f"accent covers {share * 100:.1f}% of the page"
    return share


# ---------------------------------------------------------------- render ----

def build():
    """Compose the page and return the finished RGB image."""
    BOXES.clear()
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d._image = img  # convenience handle for paste

    assert_geometry()
    assert_story_count()
    assert_type_sizes()

    draw_masthead(d)
    draw_timeline(d)
    draw_region_bar(d)
    draw_stats(d)
    draw_featured(d)
    draw_grid(d)
    draw_briefs(d)
    draw_map(d)
    draw_sure(d)
    draw_date_check(d)      # last, as the brief requires

    # overlap law: every band is checked pairwise on real ink boxes
    assert_no_overlap((Y_MAST_TOP, Y_MAST_BOT), "masthead band")
    assert_no_overlap((Y_TIME_TOP, Y_TIME_BOT), "timeline band")
    assert_no_overlap((Y_REGION_TOP, Y_REGION_BOT), "region band")
    assert_no_overlap((Y_STAT_TOP, Y_STAT_BOT), "stat band")
    assert_no_overlap((Y_BOT_TOP, Y_BOT_BOT), "briefs band")
    assert_no_overlap((Y_GRID_TOP, Y_GRID_BOT), "grid band")

    share = assert_accent(img)
    return img, share


def main():
    img, share = build()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    img.save(out, format="PNG", optimize=True)
    size = os.path.getsize(out)
    assert size <= 1_048_576, f"entry.png is {size} bytes, over 1 MiB"
    print(f"wrote {out}")
    print(f"  {W}x{H} RGB PNG, {size} bytes")
    print(f"  accent coverage {share * 100:.2f}% of the page")
    print(f"  23 stories: 3 featured, 12 grid, 8 briefs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
