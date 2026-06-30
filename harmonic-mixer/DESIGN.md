# Harmonizer — Design System

The visual language for Harmonizer. Read this before building any new screen, component, or marketing surface so the product stays consistent.

The short version: **monochrome base, one loud accent, lots of empty space, and a record-shop vocabulary.** When in doubt, take something away.

---

## 1. Design direction

Harmonizer borrows the visual discipline of underground dance-music labels — specifically the **TSZR (Three Six Zero Recordings)** record-sleeve aesthetic. The defining traits:

- **Restraint over decoration.** Black on white, generous negative space, the artwork (or the data) does the talking. Nothing is added that doesn't carry meaning.
- **A record-shop vocabulary.** Catalog numbers, side labels, pressing stamps, dot-matrix lettering, vinyl center stickers. The product is a DJ tool, so it should look like it came out of a crate, not a SaaS template.
- **One high-energy accent, used sparingly.** Everything is monochrome *except* the single Ferrari-red accent, so when red appears it always means something (a match, a primary action, the current track).
- **Lowercase utility labels.** Section headers and metadata are lowercase and quiet ("how it works", "compatible next tracks"), the way a label prints liner notes.

The automotive palette (Ferrari red + Nardo grey are both car colors) gives us a secondary motif: precision instrumentation. Readouts can look like gauges and clusters.

---

## 2. Color

Four colors. That's the whole system. Resist adding more.

| Token | Hex | Role |
|---|---|---|
| `--black` | `#0A0A0A` | Primary text, dark surfaces, vinyl body, structure |
| `--white` | `#FAFAFA` | Page background, text on dark, vinyl label spindle |
| `--red` | `#FF2800` | **Accent only** — primary CTAs, current/playing state, matches, step numerals, dot accents |
| `--nardo` | `#6E7479` | Secondary text, captions, metadata, inactive/off-key states |

Supporting neutrals (derive from the above, don't introduce new hues):

| Token | Hex | Role |
|---|---|---|
| `--nardo-light` | `#D1D4D6` | Muted text on dark backgrounds |
| `--surface-dark` | `#17181A` | Cards/tiles on a black section |
| `--stroke-dark` | `#2E3033` | Hairline borders on dark surfaces |
| `--groove` | `#1F2022` | Vinyl grooves, subtle dividers on black |

### Rules
- **Red is never decorative.** If red appears, it must signal a primary action, the active/now state, or a harmonic match. Two red things competing for attention on one screen is a bug.
- Body text is `--nardo` on white, `--nardo-light` on black. Headlines are `--black` on white, `--white` on black.
- No gradients, no shadows-as-style, no extra accent colors. The only "glow" allowed is the faint red sheen groove on the vinyl.

---

## 3. Typography

Three families, three jobs. Don't reach for a fourth.

| Role | Family | Weights | Used for |
|---|---|---|---|
| **Display** | Space Grotesk | Bold | Headlines, hero, section titles, logo |
| **Body / UI** | Inter | Regular, Medium, Semi Bold | Paragraphs, buttons, nav, labels |
| **Data / mono** | JetBrains Mono | Medium, Bold | Camelot codes (8A → 9A), BPM, catalog numbers, spec strips |

### Scale (desktop)

| Token | Size / line-height | Use |
|---|---|---|
| `display-xl` | 76 / 92, tracking −2% | Hero headline |
| `display-lg` | 64 / 72, tracking −2% | Footer / section hero |
| `title` | 30 / normal, tracking −1% | Card + step titles |
| `body-lg` | 19 / 30 | Hero subtitle, lead paragraphs |
| `body` | 16 / 26 | Standard body copy |
| `data-lg` | 30–34, mono | Key readouts on the vinyl / slider |
| `label` | 14 / normal, tracking +4%, **lowercase** | Eyebrows, section markers |
| `caption` | 10–13, mono, tracking +1% | Metadata, catalog numbers, spec strip |

### Rules
- **Mono is reserved for data.** Anything that is a key, tempo, count, or catalog number is JetBrains Mono. Prose never is.
- Section markers / eyebrows are **lowercase**, letter-spaced, in `--nardo`. Always preceded by an 8px red dot when introducing a section.
- Headlines are tight (negative tracking). Captions and labels are loose (positive tracking). This contrast is part of the identity.

---

## 4. Layout

- **Grid:** 1440px desktop frame, 64px left/right page margins, 32px gutter between columns.
- **Rhythm:** sections breathe — 96–120px vertical padding on major sections. Empty space is a feature, not waste.
- **Section bands alternate** white and black to chapter the page. A black band signals "interactive / data" (the slider, the footer); white bands are editorial (hero, how-it-works, dot-matrix).
- **Zero or minimal border-radius** on structural elements (cards, buttons, tiles) — squared corners read like print. Radius is reserved for things that are *literally round* (the vinyl, the tube numeral rings, the red status dot).
- Dividers are **hairlines** (1–2px), never heavy rules.

---

## 5. Signature elements

These four motifs are what make it Harmonizer. Reuse them; don't invent new ones for the same job.

### 5.1 The vinyl record
The hero centerpiece and the product's mascot. A grooved black disc with a **Ferrari-red center label** acting as the data sticker.
- Concentric grooves: thin `--groove` rings stepping inward (~14px apart).
- Center label is red, ringed in black, with a small spindle hole in the middle.
- Label content reads like a real pressing, top to bottom: product/track name (Space Grotesk Bold, white), a mono sub-line ("side a · harmonic mix"), a play triangle, the big mono readout (`8A → 9A`), a mono status line (`124 BPM · PERFECT MATCH`), and a catalog number (`HZ—001`).
- **When to use:** hero moments, empty states, loading, "now playing." One per screen, max.

### 5.2 The Camelot slider
The interactive heart — a horizontal, swipeable strip of key cards that replaces a static wheel.
- Each card: large mono key code (`8A`), mono BPM beneath, and a status pill.
- **Three states**, encoded by color:
  - `playing` — solid red card, black pill. The current track. Exactly one.
  - `match` — dark card, **red pill**, white key. Harmonically compatible.
  - `off-key` — dark card, grey pill, grey key. Incompatible / dimmed.
- Lives on a **black band**. Include a "→ drag" affordance.
- **When to use:** anywhere the user picks or browses the next track. This is the core UI pattern — a track list, search results, and the mixing view should all reuse it.

### 5.3 Dot-matrix lettering
TSZR's punch-card / pressing-stencil type, built from a literal **5×7 grid of dots** per letter.
- Lit dots `--black`, unlit dots a faint grey (`#E6E6E6`) so the grid is visible.
- For big statement words only (section headers like "HARMONIZER", milestone numbers). Never for body copy or anything that needs to be read fast.
- **When to use:** one big graphic moment per page. It's a spice, not a staple.

### 5.4 Tube numerals
Rounded "paperclip" numbers echoing TSZR catalog numerals (the fat `0056` look).
- Implemented as a digit inside a thick rounded **red ring** (6px stroke, fully rounded).
- **When to use:** step sequences (how-it-works 1/2/3), ordered lists, version/catalog call-outs. Only where order genuinely matters.

---

## 6. Components

### Buttons
- **Primary:** solid `--red` fill, white Semi Bold label, trailing `→`, squared corners, ~28px / 16px padding. One per view.
- **Secondary / ghost:** transparent, 1.5px `--black` border, black label, no arrow.
- **Nav CTA:** solid `--black`, white label, compact padding.
- The `→` arrow is a recurring motif — use it on forward actions and links, never on a ghost/secondary.

### Cards & tiles
- Squared corners. On white: hairline top-rule + content. On black: `--surface-dark` fill, `--stroke-dark` 1px border.
- Status pills inside cards: small, squared, lowercase label, letter-spaced. Color encodes meaning (see slider states).

### Section header pattern
Every major section opens the same way: an **8px red dot + lowercase letter-spaced label** in `--nardo`. This is the connective tissue across the whole product.

---

## 7. Voice & copy

- **Sentence case or lowercase**, never Title Case or shouting. Labels lowercase; headlines sentence case.
- Plain, confident, a little bit record-shop. "scan your crate", "stop guessing. start mixing.", "pressed from your library."
- Name things by what the user controls: "scan", "mix", "the wheel" — not "ingest", "process", "algorithm output".
- The `→` belongs in copy too: "stream →", "see how it works →".
- Privacy is a selling point — say it plainly ("100% local — your files never leave"), and that line is allowed to be red.

---

## 8. Quick-reference tokens

```css
:root {
  /* color */
  --black: #0A0A0A;
  --white: #FAFAFA;
  --red: #FF2800;       /* accent only */
  --nardo: #6E7479;
  --nardo-light: #D1D4D6;
  --surface-dark: #17181A;
  --stroke-dark: #2E3033;
  --groove: #1F2022;

  /* type */
  --font-display: "Space Grotesk", sans-serif;
  --font-body: "Inter", sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  /* layout */
  --page-margin: 64px;
  --gutter: 32px;
  --section-pad: 96px;
  --radius-structural: 0px;   /* squared corners by default */
}
```

## 9. Do / Don't

**Do**
- Keep red rare and meaningful.
- Use mono for every number.
- Open sections with the red-dot + lowercase label.
- Let sections breathe; alternate white/black bands.
- Reuse the four signature elements for their assigned jobs.

**Don't**
- Add a fifth color or a third display font.
- Round structural corners or add drop shadows.
- Use dot-matrix or tube numerals for fast-read content.
- Put two primary (red) actions in one view.
- Title Case anything.
