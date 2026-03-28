# SimSEO — Interface Design System

## Direction & Feel

**Audience:** Non-technical users — small business owners, bloggers, marketers. Not developers.
**Feel:** Editorial report. A trusted advisor's printed findings. Clear, warm, readable — not a dashboard, not a terminal.
**Mental model:** The score is the headline. The hints are the annotated findings. Color only appears when it means something.

---

## Fonts

- **DM Serif Display** (weight 400) — product name, score number, metric section headings, verdict text. Provides editorial weight and magazine-quality hierarchy.
- **Inter** (weights 400, 500, 600) — all body text, labels, buttons, tabs.

Load via Google Fonts:
```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600&display=swap" />
```

---

## Tokens

```css
/* Text hierarchy */
--ink-1: #18181b;   /* primary — headlines, body */
--ink-2: #3f3f46;   /* secondary — recommendations, supporting text */
--ink-3: #71717a;   /* tertiary — descriptions, metadata */
--ink-4: #a1a1aa;   /* muted — placeholders, disabled, faint labels */

/* Surfaces */
--surface-0: #faf9f7;   /* page background — warm cream */
--surface-1: #ffffff;   /* card surface */
--surface-2: #f5f3f0;   /* input background, inner sections */

/* Borders */
--border-soft: #e4e0da;   /* standard card separation */
--border-mid:  #d0cbc4;   /* input borders, slightly more visible */

/* Brand */
--brand:       #2d5be3;   /* links only */
--brand-hover: #1d4ed8;

/* Semantic — good */
--good:           #15803d;
--good-surface:   #f0fdf4;
--good-border:    #bbf7d0;

/* Semantic — warning */
--warn:           #92400e;
--warn-surface:   #fffbeb;
--warn-border:    #fde68a;

/* Semantic — critical */
--critical:         #991b1b;
--critical-surface: #fef2f2;
--critical-border:  #fecaca;

/* Semantic — info */
--info:           #1e40af;
--info-surface:   #eff6ff;
--info-border:    #bfdbfe;
```

---

## Depth Strategy

**Borders only.** No drop shadows on cards or panels.

- Cards: `border: 1px solid var(--border-soft)` on `var(--surface-1)`
- Inputs: `border: 1px solid var(--border-mid)` on `var(--surface-2)` (inset feel)
- Focus ring: `box-shadow: 0 0 0 3px rgba(45, 91, 227, 0.1)` + `border-color: var(--brand)`
- Page background: `var(--surface-0)` warm cream — one step warmer than cards

---

## Spacing

Base unit: `4px` (0.25rem). Scale in use:
- `0.3rem` — label-to-input gap
- `0.5rem` — between hint header elements
- `0.75rem` — between hint items
- `1rem` — form field gap
- `1.25rem` — between cards
- `1.75rem` — card padding
- `2rem` — score card internal gap

---

## Typography Scale

| Role | Font | Size | Weight | Notes |
|------|------|------|--------|-------|
| Product name | DM Serif Display | 1.9rem | 400 | Header masthead |
| Score number | DM Serif Display | 2.4rem | 400 | Inside ring |
| Score verdict | DM Serif Display | 1.35rem | 400 | Colored by grade |
| Metric heading | DM Serif Display | 1.05rem | 400 | Tab section h3 |
| Section label | Inter | 0.75rem | 600 | Uppercase, tracked 0.07–0.09em |
| Body / hint message | Inter | 0.9rem | 600 | Hint message line |
| Body / recommendation | Inter | 0.85rem | 400 | Hint detail |
| Tab buttons | Inter | 0.85rem | 500/600 | 600 when active |
| Filter buttons | Inter | 0.75rem | 600 | Uppercase, tracked |

---

## Signature Component — Score Ring

SVG circular progress ring. The SEO score is displayed inside as a large DM Serif Display number. Below the ring (outside), an editorial verdict in serif colored by grade.

```html
<div class="score-ring-wrap">
  <svg class="score-ring" viewBox="0 0 120 120" aria-hidden="true">
    <circle class="score-ring-bg" cx="60" cy="60" r="52" />
    <circle class="score-ring-fill" cx="60" cy="60" r="52" id="score-ring-fill" />
  </svg>
  <div class="score-ring-inner">
    <span class="score-number" id="score-display">--</span>
  </div>
</div>
```

Key values:
- `r="52"` → circumference = `326.73` (2π × 52)
- Ring starts at top: `transform: rotate(-90deg)` on the SVG
- Stroke width: `7`
- Animation: `stroke-dashoffset` from `326.73` → `326.73 * (1 - score/100)`
- Easing: `cubic-bezier(0.4, 0, 0.2, 1)` over `0.9s`

Stroke colors by grade:
- `good` (≥80): `var(--good)` — `#15803d`
- `average` (≥50): `#d97706`
- `poor` (<50): `var(--critical)` — `#991b1b`

Verdict text grades:
- ≥80 → "Good standing"
- ≥50 → "Needs improvement"
- <50  → "Significant issues"

---

## Component Patterns

### Cards
```css
.card {
  background: var(--surface-1);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 1.75rem;
}
```

### Labels (form fields, section headers)
```css
label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--ink-3);
}
```

### Primary button (one per form)
```css
/* Ink-black, not branded color */
background: var(--ink-1);
color: #fff;
border-radius: 6px;
font-weight: 600;
/* hover: var(--ink-2), disabled: var(--ink-4) */
```

### Tabs
- Active: `color: var(--ink-1)`, `border-bottom: 2px solid var(--ink-1)`, weight 600
- Inactive: `color: var(--ink-3)`, weight 500
- No colored accent — ink-black active state

### Hint items
Tinted surface + matching border by severity. No left accent stripe.
```css
.hint-item.critical { background: var(--critical-surface); border-color: var(--critical-border); }
.hint-item.warning  { background: var(--warn-surface);     border-color: var(--warn-border); }
.hint-item.info     { background: var(--info-surface);     border-color: var(--info-border); }
```

Badges: `font-size: 0.65rem`, uppercase, tracked, `border-radius: 3px` — stamp-like, not pill.

### Progress bars (AI metrics)
Height `5px`, no border, rounded. Same good/average/poor color scale as ring.

---

## What Was Rejected & Why

| Default | Replaced with | Reason |
|---------|--------------|--------|
| White cards on `#f4f6fb` gray | White cards on `#faf9f7` warm cream | Cool gray reads technical; warm cream reads paper/editorial |
| Indigo `#667eea` accent button | Ink-black button | Branded color = product marketing; ink-black = trusted tool |
| `system-ui` everywhere | DM Serif Display for display text | Serif gives editorial authority at hero sizes |
| Purple active tab indicator | Ink-black active tab | Consistent with "ink on paper" metaphor |
| Left accent stripe on hints | Tinted surface + matching border | Stripes feel like a dev tool; tinted surfaces feel like annotated notes |
| Big raw score number floating in card | Score ring with serif number + verdict | Ring communicates progress/grade at a glance without feeling like a gauge |
