# `game_brief.json` — schema and example

The brief is the **structured definition of the game's design intent**
— theme, palette, style lock, tier plan, full symbol manifest. It's
the human-readable counterpart to the runtime canonical state in
`project.json` (which embeds the same brief under
`project.json.brief` and adds the asset registry, counters,
timestamps, and `style_anchor` fields on top).

When art skills generate, they read **`project.json`** as the runtime
canonical source — that's where `style_anchor.text`,
`style_anchor.key_art_path`, and the per-symbol asset records live.
`game_brief.json` mirrors the brief portion for human readability
(designers can scan it without parsing the full project state) and
carries optional mirror fields (`style_anchor`, `key_art_path`) for
the same reason.

Keep this file small, named-color only, and locked once approved.
Both files should agree on the brief contents at all times; if they
disagree, `project.json` wins.

## Schema (JSON)

```json
{
  "schema": "slot_game_brief.v1",
  "game_name": "string — user-facing theme name, NEVER the internal codename",
  "mood": "string — 1–2 words, e.g. 'mystical serene', 'aggressive electric'",
  "theme_summary": "string — ≤ 2 sentences",
  "style_lock": "string — EXACTLY one phrase from shared/nb2_prompting.md §9.4",
  "palette_leads": {
    "primary": "string — named colors, e.g. 'warm crimson and antique gold'",
    "accents": "string — 1–2 named accent colors",
    "forbidden_on_lp": ["gold", "amber", "warm orange", "..."]
  },
  "grid": "string — e.g. '5x3', '5x4', '5x6_bonus'",
  "tier_plan": {
    "lp_family": "one of: card_royals | suits | themed_objects | gems",
    "lp_count": 5,
    "mp_count": 2,
    "hp_count": 2,
    "specials_count": 3
  },
  "wild": {
    "category": "string — what it IS, e.g. 'WILD text label', 'lightning bolt object', 'character'",
    "breaks_theme_via": "string — how it breaks: different category / electric color / etc."
  },
  "scatter": {
    "label": "string — usually 'SCATTER' or 'BONUS'",
    "shape": "string — 'circular badge' (default) or other"
  },
  "bonus": {
    "label": "string — read by BONUS_TRIGGER_TEMPLATE.md, e.g. 'BONUS', 'FEATURE'",
    "subject": "string — the themed object the BO trigger renders as, e.g. 'ancient sealed scroll', 'crystal orb'"
  },
  "coins": [
    {
      "id":      "WY1",
      "color":   "gold",
      "mechanic": "standard hold-and-spin coin",
      "notes":   "optional"
    }
  ],
  "//": "coins[] — read by COIN_TEMPLATE.md. One entry per WY1..WY4. Default is WY1 gold; override per game.",
  "banners": [
    {
      "tier":  "big",
      "label": "BIG WIN",
      "min_multiplier": 10
    }
  ],
  "//": "banners[] — read by BANNERS_TEMPLATE.md. tier is one of small/medium/big/mega/epic.",
  "multipliers": [2, 3, 5, 10],
  "//": "multipliers[] — denominations needed in the game. Used by MULTIPLIER_TEMPLATE.md and SPECIAL_MECHANICS_TEMPLATE.md.",
  "jackpot_tier_names": {
    "JP1": "Grand",
    "JP2": "Major",
    "JP3": "Minor",
    "JP4": "Mini"
  },
  "//": "jackpot_tier_names — EXPLICIT mapping of JP<N> prefix to the tier name it represents IN THIS SPECIFIC GAME. Newer H5G games (Tesla, Chevy family, Billionaire's series, Blazing Stampede) use JP1=Grand; some older games use JP1=Mini. The catalog of 26 shipped games shows 9 of 11 numeric-jackpot games use JP1=Grand. Always set this field explicitly; the templates read it to know which slice/medallion gets which label and metallic finish. For 6-tier games extend to JP5, JP6 with 'Mega' / 'Premium' or theme-specific labels. For Bronze/Silver/Gold/Platinum, Hourly/Daily/Anytime, or other variant naming, use those strings instead.",
  "symbol_manifest": [
    {
      "id": "HP1",
      "tier": "HP",
      "family": "HP",
      "subject": "phoenix character bust",
      "role": "high-pay character",
      "mechanic": "standard pay",
      "notes": "optional notes"
    }
  ],

  "//": "Full prefix vocabulary + family list lives in shared/symbol_vocabulary.md.",
  "//": "Manifest entry shape: {id, tier, family, subject, role, mechanic, notes}.",
  "//": "  id       — literal prefix as the filename label (e.g. HP1, BWY1, WJP1). Becomes Symbol_Art/<id>_NNN.png.",
  "//": "  tier     — one of: 'HP', 'MP', 'LP', 'special'.",
  "//": "  family   — visual family for routing. One of: HP, MP, LP, Wild, Scatter, WYS, SF, BO, Blocker, Jackpot, Pachinko, Replacement, SpecialMechanics. The art skill picks the template file from this.",
  "//": "  subject  — user-facing thematic noun ('phoenix bust', 'red coin', 'crystal ball'). Drives the descriptive part of the prompt.",
  "//": "  role     — short human-readable description of what the symbol does (optional but useful).",
  "//": "  mechanic — the ROUTING KEY. The family template's 'brief-driven roles' table looks this up to pick which overlay cues to apply on top of the family base. For HP/MP/LP this can stay 'standard pay'; for WY/SF/JP/compound prefixes it disambiguates which role overlay applies.",
  "//": "  notes    — anything else worth carrying through (variant references, art callouts).",
  "//": "Common prefixes:",
  "//": "  HP1-HP4 (high-pay), MP1-MP3 (mid-pay), LP1-LP6 (low-pay)",
  "//": "  WD / WD2+ (wild + 9 variants), SW (scatter-wild hybrid)",
  "//": "  SC (legacy scatter), WY1-WY10+, WYS1-WYS2+ (WYS family — coin / portal / spherical with 8 brief-driven roles)",
  "//": "  BO (bonus trigger), BAG / BAG_BO (money bag scatters), MOJ (money emoji)",
  "//": "  COL (collector), ACT (activator)",
  "//": "  HOT_x* / HOT_ADD / HOT_COMB / HOT_COLLAPSE / HOT_PERSIST (Loot Link operators)",
  "//": "  SF, SF1-SF11+ (SF family — special-feature tokens with 13 brief-driven roles)",
  "//": "  BL, BL1, BL2+ (blocker / placeholder; numbered for multi-mode games)",
  "//": "  JP1-JP6 (jackpot tiers — 4-tier or 6-tier; numeric ordering per brief.jackpot_tier_names)",
  "//": "  D2_<base>, D3_<base>, SPLIT_<base>, DHP, MULT_x* (pay multipliers + double-HP alias)",
  "//": "  R, R1+ (replacement / runtime swap)",
  "//": "  BALL / PEG / BUCKET_x* (pachinko / drop-style games)",
  "//": "Compound prefixes (each is a first-class symbol with its own <PREFIX>_NNN.png filename):",
  "//": "  BWY, BWY1+   — Bonus + WYS (route to COIN_TEMPLATE.md + bonus overlay)",
  "//": "  WJP, WJP1+   — Wild + Jackpot (route to WILD_VARIANTS_TEMPLATE.md + jackpot overlay)",
  "//": "  WDWY, WDWY1+ — Wild + WYS / scatter-wild hybrid (Chevy pattern)",
  "//": "  WDSF, WDSF1+ — Wild + SF (Chevy-Alt pattern)",
  "//": "  MUWD, MUWD1+ — Multiplier Wild (Honda pattern; alias for the multiplier-wild variant)",
  "//": "  MUWDBO+      — Multiplier Wild + Bonus framing",
  "//": "  SFWY, SFWY1+ — SF + WYS (route to MYSTERY_TEMPLATE.md + WYS visual notes)",
  "export_background_policy": {
    "hp": "black",
    "mp": "black",
    "lp": "white",
    "wild": "black",
    "scatter": "black"
  },
  "style_anchor": "string | null — 60–90-word block from /slot-step-01; this is a human-readable mirror of project.json.style_anchor.text (which is the canonical location every downstream skill reads)",
  "key_art_path": "string | null — bare filename of the locked key art; human-readable mirror of project.json.style_anchor.key_art_path (the canonical location). Written by /slot-step-02 on approval.",
  "gdd_source": {
    "file_id": "string | null — Google Drive file ID; set by /slot-step-00",
    "file_name": "string | null — full filename including version and extension",
    "drive_url": "string | null — https://drive.google.com/file/d/<ID>/view",
    "version_extracted": "string | null — version string from filename or doc header",
    "extracted_at": "string | null — ISO date when the GDD was last read"
  },
  "mode_list": ["string — e.g. 'base game', 'free spins', 'bonus pick-me', 'wheel'"],
  "rtp": "string | null — e.g. '96.5%'; for reference only, not used in art prompts",
  "open_questions": [
    "string — anything missing from the GDD or undecided"
  ]
}
```

## Example: a fully-locked brief

```json
{
  "schema": "slot_game_brief.v1",
  "game_name": "Phoenix of Ardashir",
  "mood": "mystical regal",
  "theme_summary": "Ancient Persian palace courtyard with a sacred phoenix presiding over a star-filled night sky.",
  "style_lock": "stylized semi-realistic slot game art",
  "palette_leads": {
    "primary": "deep midnight indigo with antique gold and burning crimson",
    "accents": "lapis blue, ember orange",
    "forbidden_on_lp": ["gold", "amber", "warm orange", "crimson"]
  },
  "grid": "5x4",
  "tier_plan": {
    "lp_family": "card_royals",
    "lp_count": 5,
    "mp_count": 2,
    "hp_count": 2,
    "specials_count": 3
  },
  "wild": {
    "category": "WILD text label rendered as molten gold calligraphy",
    "breaks_theme_via": "electric cyan rim light that appears nowhere else in the palette; text breaks the character/object pattern of the rest of the set"
  },
  "scatter": {
    "label": "SCATTER",
    "shape": "circular badge with radiant burst"
  },
  "jackpot_tier_names": {
    "JP1": "Grand",
    "JP2": "Major",
    "JP3": "Minor",
    "JP4": "Mini"
  },
  "symbol_manifest": [
    {"id": "HP1",  "tier": "HP",      "family": "HP",       "subject": "phoenix bust facing front, wings spread",                "role": "high-pay character",      "mechanic": "standard pay"},
    {"id": "HP2",  "tier": "HP",      "family": "HP",       "subject": "King Ardashir bust in profile",                          "role": "high-pay character",      "mechanic": "standard pay"},
    {"id": "MP1",  "tier": "MP",      "family": "MP",       "subject": "ornate brass oil lamp",                                  "role": "mid-pay object",          "mechanic": "standard pay"},
    {"id": "MP2",  "tier": "MP",      "family": "MP",       "subject": "carved cedar chest with lapis inlay",                    "role": "mid-pay object",          "mechanic": "standard pay"},
    {"id": "LP1",  "tier": "LP",      "family": "LP",       "subject": "letter A as cool muted card royal",                      "role": "low-pay card",            "mechanic": "standard pay"},
    {"id": "LP2",  "tier": "LP",      "family": "LP",       "subject": "letter K as cool muted card royal",                      "role": "low-pay card",            "mechanic": "standard pay"},
    {"id": "LP3",  "tier": "LP",      "family": "LP",       "subject": "letter Q as cool muted card royal",                      "role": "low-pay card",            "mechanic": "standard pay"},
    {"id": "LP4",  "tier": "LP",      "family": "LP",       "subject": "letter J as cool muted card royal",                      "role": "low-pay card",            "mechanic": "standard pay"},
    {"id": "LP5",  "tier": "LP",      "family": "LP",       "subject": "10 as cool muted card royal",                            "role": "low-pay card",            "mechanic": "standard pay"},
    {"id": "WD1",  "tier": "special", "family": "Wild",     "subject": "WILD text label in molten gold with electric cyan rim",  "role": "wild — standard",         "mechanic": "standard wild"},
    {"id": "WD2",  "tier": "special", "family": "Wild",     "subject": "WILD text label with chains and lock motif",             "role": "wild — sticky variant",   "mechanic": "sticky wild"},
    {"id": "WY1",  "tier": "special", "family": "WYS",      "subject": "gold phoenix-engraved coin",                             "role": "hold-and-spin coin",      "mechanic": "hold-and-spin coin"},
    {"id": "WY2",  "tier": "special", "family": "WYS",      "subject": "red phoenix-engraved coin with energy crackle",          "role": "random-wilds shooter",    "mechanic": "random wilds shooter"},
    {"id": "WY3",  "tier": "special", "family": "WYS",      "subject": "green phoenix-engraved coin with collector aesthetic",   "role": "collector + multiplier",  "mechanic": "collector + multiplier"},
    {"id": "BO",   "tier": "special", "family": "BO",       "subject": "ancient sealed scroll with phoenix wax seal",            "role": "bonus trigger",           "mechanic": "free spins trigger"},
    {"id": "SF1",  "tier": "special", "family": "SF",       "subject": "shrouded crystal with hidden glow",                      "role": "mystery transform",       "mechanic": "mystery transform"},
    {"id": "BL",   "tier": "special", "family": "Blocker",  "subject": "cracked obsidian shard with dead-cold finish",           "role": "blocker — does not pay",  "mechanic": "blocker"},
    {"id": "JP1",  "tier": "special", "family": "Jackpot",  "subject": "Grand jackpot medallion in platinum",                    "role": "jackpot tier — Grand",    "mechanic": "jackpot tier — Grand"},
    {"id": "JP2",  "tier": "special", "family": "Jackpot",  "subject": "Major jackpot medallion in warm gold",                   "role": "jackpot tier — Major",    "mechanic": "jackpot tier — Major"},
    {"id": "JP3",  "tier": "special", "family": "Jackpot",  "subject": "Minor jackpot medallion in silver",                      "role": "jackpot tier — Minor",    "mechanic": "jackpot tier — Minor"},
    {"id": "JP4",  "tier": "special", "family": "Jackpot",  "subject": "Mini jackpot medallion in bronze",                       "role": "jackpot tier — Mini",     "mechanic": "jackpot tier — Mini"},
    {"id": "BWY1", "tier": "special", "family": "WYS",      "subject": "bonus phoenix coin with sealed-scroll motif",            "role": "bonus trigger + coin",    "mechanic": "bonus trigger + coin payout"}
  ],
  "export_background_policy": {
    "hp": "black",
    "mp": "black",
    "lp": "white",
    "wild": "black",
    "scatter": "black"
  },
  "open_questions": []
}
```

## Anti-patterns

```json
{
  "game_name": "Tesla 4470",                              // INTERNAL CODENAME — wrong
  "palette_leads": { "primary": "#C8960C and #4A1818" }, // HEX — wrong
  "style_lock": "stylized + painterly + cel-shaded",     // multiple — wrong
  "tier_plan": { "lp_family": "cards + gems" }           // mixed family — wrong
}
```
