# 🎨 MarkaJiap Design System
> Use this guide to create matching websites with the exact same "Thai Lucky Color" theme.

## 1. Typography (ตัวอักษร)
We use a combination of **Prompt** (for modern Thai) and **IBM Plex Sans** (for English/Code).

```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Prompt:wght@300;400;500;600;700&display=swap');

body {
  font-family: 'Prompt', 'IBM Plex Sans', -apple-system, sans-serif;
}
```

---

## 2. Color Palette (ชุดสีมงคล)
Based on Thai Astrology for Sunday-born individuals (Purple & Gold).

### Primary Colors
| Name | Hex | CSS Variable | Usage |
|------|-----|--------------|-------|
| **Luck Purple** | `#7B2D8E` | `--purple` | Primary Brand, Borders |
| **Success Gold** | `#D4A634` | `--gold` | Accents, Buttons, Highlights |
| ** Deep Purple** | `#5B1D6E` | `--purple-dark` | Gradients End |
| **Bright Gold** | `#E4B644` | `--gold-light` | Button Hover, Links |

### Neutrals (Backgrounds)
| Name | Hex | CSS Variable | Usage |
|------|-----|--------------|-------|
| BG Primary | `#0D0A12` | `--bg-primary` | Main Background |
| BG Secondary | `#1A1625` | `--bg-secondary` | Cards, Sections |
| BG Tertiary | `#241F30` | `--bg-tertiary` | Nav, Headers |
| Text Primary | `#F0EDF5` | `--text-primary` | Headings, Body |
| Text Muted | `#A09AAD` | `--text-secondary` | Subtitles, Meta |

---

## 3. Gradients & Effects
Copy these exact CSS rules for the "Glow" and "Premium" look.

```css
:root {
  /* Brand Gradients */
  --gradient-purple: linear-gradient(135deg, #7B2D8E 0%, #5B1D6E 100%);
  --gradient-gold: linear-gradient(135deg, #D4A634 0%, #E4B644 100%);
  --gradient-hero: linear-gradient(135deg, #7B2D8E 0%, #D4A634 50%, #7B2D8E 100%);
}

/* Text Gradient Effect */
.gradient-text {
  background: var(--gradient-hero);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient-shift 4s ease infinite;
}
```

---

## 4. UI Components

### Buttons
**Primary (Gold Action)**
```css
.btn-primary {
  background: var(--gradient-gold);
  color: #1A1625;
  font-weight: 600;
  border-radius: 8px;
  padding: 12px 24px;
  border: none;
  /* Glow Effect on Hover */
  box-shadow: 0 8px 24px rgba(212, 166, 52, 0.4); 
}
```

**Secondary (Dark Outline)**
```css
.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
```

### Cards (Glass/Dark)
```css
.card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color); /* #2A243A */
  border-radius: 16px;
}

.card:hover {
  transform: translateY(-4px);
  border-color: var(--purple);
  box-shadow: 0 16px 48px rgba(123, 45, 142, 0.2);
}
```

---

## 5. Layout System
Standard spacing variables to keep rhythm.

```css
:root {
  --container-max: 1200px;
  --section-padding: 100px;  /* Desktop */
  --mobile-padding: 60px;    /* Mobile */
}

.container {
  max-width: var(--container-max);
  margin: 0 auto;
  padding: 0 24px;
}
```

---

## 6. Quick Start Template
Save this as `theme.css` to instantly apply the look.

```css
/* Base Variables */
:root {
  --purple: #7B2D8E; --gold: #D4A634;
  --bg-primary: #0D0A12; --bg-secondary: #1A1625;
  --text-primary: #F0EDF5; --text-secondary: #A09AAD;
  --border-color: #2A243A;
  --gradient-gold: linear-gradient(135deg, #D4A634 0%, #E4B644 100%);
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Prompt', sans-serif;
  line-height: 1.6;
}

h1, h2, h3 { color: var(--text-primary); font-weight: 700; }
a { color: var(--gold); text-decoration: none; }
```
