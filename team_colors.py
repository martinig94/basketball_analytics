"""EuroLeague team colour palettes.

Each :class:`TeamPalette` stores the six colours that drive every visual
element of the scouting report: the MkDocs site, the matplotlib figures,
and the PDF export.

Colour fields
-------------
primary
    The team's main accent / highlight colour (badge, headings, borders).
bg_darkest
    Deepest dark background (page canvas, code blocks).
bg_header
    Header / navigation bar background.
bg_mid
    Mid-level surface (h2 banners, table even rows).
bg_light
    Lighter surface (table odd rows, alternate panels).
text_on_primary
    Foreground colour when text is placed **on** ``primary`` (badge labels,
    dark-on-yellow or white-on-red depending on luminance).

Team codes match the EuroLeague API (season 2025 / 2024-25).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TeamPalette:
    """Immutable six-colour palette for one EuroLeague team.

    Args:
        primary: Main accent / highlight hex colour.
        bg_darkest: Deepest background hex colour.
        bg_header: Header and navigation background hex colour.
        bg_mid: Mid-level surface hex colour.
        bg_light: Lighter surface hex colour.
        text_on_primary: Text hex colour placed on ``primary`` backgrounds.
        name: Human-readable team name (informational only).
    """

    primary: str
    bg_darkest: str
    bg_header: str
    bg_mid: str
    bg_light: str
    text_on_primary: str
    name: str = ""


TEAM_COLORS: dict[str, TeamPalette] = {
    # ── ASV – LDLC ASVEL Villeurbanne (orange / dark blue) ────────────────────
    "ASV": TeamPalette(
        primary="#FF6B00",
        bg_darkest="#0A0E1C",
        bg_header="#002070",
        bg_mid="#0E1C3A",
        bg_light="#0A152E",
        text_on_primary="#0A0E1C",
        name="LDLC ASVEL Villeurbanne",
    ),
    # ── BAR – FC Barcelona (claret / blue) ────────────────────────────────────
    "BAR": TeamPalette(
        primary="#A50044",
        bg_darkest="#080812",
        bg_header="#003399",
        bg_mid="#10143D",
        bg_light="#0A0F2E",
        text_on_primary="#FFFFFF",
        name="FC Barcelona",
    ),
    # ── BAS – Baskonia Vitoria-Gasteiz (royal blue / orange) ──────────────────
    "BAS": TeamPalette(
        primary="#FF6600",
        bg_darkest="#090B1A",
        bg_header="#001F5A",
        bg_mid="#0D1A3A",
        bg_light="#08132E",
        text_on_primary="#090B1A",
        name="Kosner Baskonia Vitoria-Gasteiz",
    ),
    # ── DUB – Dubai Basketball (gold / sand) ──────────────────────────────────
    "DUB": TeamPalette(
        primary="#C9A84C",
        bg_darkest="#0D0A06",
        bg_header="#2E1F08",
        bg_mid="#221808",
        bg_light="#170F05",
        text_on_primary="#0D0A06",
        name="Dubai Basketball",
    ),
    # ── HTA – Hapoel IBI Tel Aviv (red / white) ───────────────────────────────
    "HTA": TeamPalette(
        primary="#E30613",
        bg_darkest="#0D0404",
        bg_header="#8B0000",
        bg_mid="#1F0808",
        bg_light="#140505",
        text_on_primary="#FFFFFF",
        name="Hapoel IBI Tel Aviv",
    ),
    # ── IST – Anadolu Efes Istanbul (sky blue / navy) ─────────────────────────
    "IST": TeamPalette(
        primary="#009FE3",
        bg_darkest="#050E1A",
        bg_header="#00285A",
        bg_mid="#091C38",
        bg_light="#051428",
        text_on_primary="#050E1A",
        name="Anadolu Efes Istanbul",
    ),
    # ── MAD – Real Madrid (purple / gold) ─────────────────────────────────────
    "MAD": TeamPalette(
        primary="#7533B0",
        bg_darkest="#0D070F",
        bg_header="#2D0F4A",
        bg_mid="#1F0B33",
        bg_light="#160826",
        text_on_primary="#FFFFFF",
        name="Real Madrid",
    ),
    # ── MCO – AS Monaco (red / white) ─────────────────────────────────────────
    "MCO": TeamPalette(
        primary="#E31C23",
        bg_darkest="#0D0405",
        bg_header="#8C0008",
        bg_mid="#1F0808",
        bg_light="#140505",
        text_on_primary="#FFFFFF",
        name="AS Monaco",
    ),
    # ── MIL – EA7 Emporio Armani Milan (red / black) ──────────────────────────
    "MIL": TeamPalette(
        primary="#C8102E",
        bg_darkest="#0D0608",
        bg_header="#200010",
        bg_mid="#1A0A0E",
        bg_light="#110608",
        text_on_primary="#FFFFFF",
        name="EA7 Emporio Armani Milan",
    ),
    # ── MUN – FC Bayern Munich (red / white) ──────────────────────────────────
    "MUN": TeamPalette(
        primary="#DC052D",
        bg_darkest="#0D0305",
        bg_header="#780020",
        bg_mid="#1A0509",
        bg_light="#110305",
        text_on_primary="#FFFFFF",
        name="FC Bayern Munich",
    ),
    # ── OLY – Olympiacos Piraeus (red / white) ────────────────────────────────
    "OLY": TeamPalette(
        primary="#E30613",
        bg_darkest="#0D0303",
        bg_header="#880012",
        bg_mid="#1F0606",
        bg_light="#130404",
        text_on_primary="#FFFFFF",
        name="Olympiacos Piraeus",
    ),
    # ── PAM – Valencia Basket (orange / black) ────────────────────────────────
    "PAM": TeamPalette(
        primary="#FF7700",
        bg_darkest="#0D0904",
        bg_header="#1F1000",
        bg_mid="#221500",
        bg_light="#160E00",
        text_on_primary="#0D0904",
        name="Valencia Basket",
    ),
    # ── PAN – Panathinaikos AKTOR Athens (green / black) ──────────────────────
    "PAN": TeamPalette(
        primary="#00A84F",
        bg_darkest="#050D07",
        bg_header="#004020",
        bg_mid="#0D2018",
        bg_light="#081610",
        text_on_primary="#FFFFFF",
        name="Panathinaikos AKTOR Athens",
    ),
    # ── PAR – Partizan Mozzart Bet Belgrade (black / white / silver) ──────────
    "PAR": TeamPalette(
        primary="#C8C8C8",
        bg_darkest="#0D0D0D",
        bg_header="#1A1A1A",
        bg_mid="#222222",
        bg_light="#181818",
        text_on_primary="#0D0D0D",
        name="Partizan Mozzart Bet Belgrade",
    ),
    # ── PRS – Paris Basketball (red / dark blue) ──────────────────────────────
    "PRS": TeamPalette(
        primary="#E31E24",
        bg_darkest="#07090F",
        bg_header="#0A1A6B",
        bg_mid="#0F1A40",
        bg_light="#090F30",
        text_on_primary="#FFFFFF",
        name="Paris Basketball",
    ),
    # ── RED – Crvena Zvezda Meridianbet Belgrade (red / white / blue) ─────────
    "RED": TeamPalette(
        primary="#E30613",
        bg_darkest="#0D0305",
        bg_header="#8B0000",
        bg_mid="#1F0A0A",
        bg_light="#140606",
        text_on_primary="#FFFFFF",
        name="Crvena Zvezda Meridianbet Belgrade",
    ),
    # ── TEL – Maccabi Rapyd Tel Aviv (yellow / blue) ──────────────────────────
    "TEL": TeamPalette(
        primary="#FFE033",
        bg_darkest="#07091A",
        bg_header="#001F80",
        bg_mid="#0A1540",
        bg_light="#070F2E",
        text_on_primary="#07091A",
        name="Maccabi Rapyd Tel Aviv",
    ),
    # ── ULK – Fenerbahce Beko Istanbul (gold / navy) ──────────────────────────
    "ULK": TeamPalette(
        primary="#FFD700",
        bg_darkest="#1A1A2E",
        bg_header="#00205B",
        bg_mid="#162447",
        bg_light="#0F1F3D",
        text_on_primary="#1A1A2E",
        name="Fenerbahce Beko Istanbul",
    ),
    # ── VIR – Virtus Segafredo Bologna (black / gold) ─────────────────────────
    "VIR": TeamPalette(
        primary="#C8A200",
        bg_darkest="#0D0D0D",
        bg_header="#1A1400",
        bg_mid="#1F1C0A",
        bg_light="#151206",
        text_on_primary="#0D0D0D",
        name="Virtus Bologna",
    ),
    # ── ZAL – Zalgiris Kaunas (green / white) ─────────────────────────────────
    "ZAL": TeamPalette(
        primary="#00843D",
        bg_darkest="#05100A",
        bg_header="#003D1A",
        bg_mid="#0A2214",
        bg_light="#06180E",
        text_on_primary="#FFFFFF",
        name="Zalgiris Kaunas",
    ),
}
