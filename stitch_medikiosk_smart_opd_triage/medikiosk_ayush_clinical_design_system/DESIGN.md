---
name: MediKiosk AYUSH Clinical Design System
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#3f4944'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#6f7974'
  outline-variant: '#bfc9c2'
  surface-tint: '#226a53'
  primary: '#004331'
  on-primary: '#ffffff'
  primary-container: '#0d5c46'
  on-primary-container: '#8cd2b6'
  inverse-primary: '#8ed5b9'
  secondary: '#006a63'
  on-secondary: '#ffffff'
  secondary-container: '#99efe5'
  on-secondary-container: '#006f67'
  tertiary: '#5c2f00'
  on-tertiary: '#ffffff'
  tertiary-container: '#7d4200'
  on-tertiary-container: '#ffb477'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#aaf1d4'
  primary-fixed-dim: '#8ed5b9'
  on-primary-fixed: '#002117'
  on-primary-fixed-variant: '#00513d'
  secondary-fixed: '#9cf2e8'
  secondary-fixed-dim: '#80d5cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#00504a'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: 0em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: 0em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: 0em
  body-xl:
    fontFamily: Work Sans
    fontSize: 20px
    fontWeight: '400'
    lineHeight: 30px
    letterSpacing: 0em
  body-lg:
    fontFamily: Work Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: 0em
  body-md:
    fontFamily: Work Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-sm:
    fontFamily: Work Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-lg:
    fontFamily: Work Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Work Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Work Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.03em
  code-data:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  space-2xs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  space-3xl: 4rem
  touch-min: 3.5rem
  kiosk-touch-target: 4rem
  gutter-mobile: 1rem
  gutter-tablet: 1.5rem
  gutter-desktop: 2rem
  margin-mobile: 1rem
  margin-tablet: 2rem
  margin-desktop: 3rem
---

## Brand & Style

This design system delivers a clinical, accessible, and deeply trusted interface tailored for high-volume Outpatient Departments (OPD), rural health kiosks, and specialized Ministry of AYUSH centers across India. The design language marries modern clinical rigor with traditional holistic care principles:

- **Tone & Mood:** High-trust, serene, authoritative, and compassionate. It eliminates clinical anxiety while maintaining operational speed and institutional dignity.
- **Visual Aesthetic:** Modern clinical minimalism infused with subtle tactile clarity. Crisp structural cards, elevated contrast ratios, generous touch points, and deliberate chromatic signaling ensure frictionless navigation for both junior medical officers and semi-literate, elderly rural patients.
- **Inclusive Accessibility:** Built ground-up for high-ambient-light kiosk screens, varying display resolutions, and cognitive accessibility across multilingual patient cohorts.

## Colors

The color palette grounds traditional Indian medicine (Ayurveda, Yoga, Naturopathy, Unani, Siddha, and Homeopathy) within an exacting modern clinical framework:

- **Primary (`#0D5C46` - Deep AYUSH Emerald):** Symbolizes vitality, herbal heritage, and equilibrium. Utilized for primary navigation bars, dominant action buttons, patient identity verification anchors, and verified case signatures.
- **Secondary (`#0F766E` - Clinical Teal):** Represents empirical precision and clinical diagnostics. Used for secondary actions, interactive data controls, active tab headers, and diagnostic section toggles.
- **Tertiary (`#D97706` - Warm Saffron Amber):** A culturally resonant, high-visibility cue. Employed for system alerts, pending vitals, AYUSH constitution indicators (e.g., *Prakriti* markers), triage warnings, and dosage timing cues.
- **Neutral (`#1E293B` - Deep Slate Ink):** Delivers uncompromising legibility and contrast against high-brightness clinic monitors and sunlit kiosk displays.
- **Surface & Backgrounds:** The base app background is set to a crisp, clinical soft-tint (`#F8FAFC`), paired with pure card surfaces (`#FFFFFF`) and delicate herbal-tinted subtle fills (`#F0FDF4` for normal ranges, `#FEF3C7` for review alerts, and `#FEF2F2` for critical contraindications).
- **Accessibility & Contrast:** All core interactive and body text pairings achieve a minimum contrast ratio of 7:1 against their backgrounds, exceeding WCAG 2.1 AAA requirements.

## Typography

Typography balances clinical warmth, structural authority, and extreme reading comfort:

- **Headlines (`Plus Jakarta Sans`):** Features welcoming, humanist geometry with modern terminals. This prevents the clinical portal from feeling intimidating, making kiosk interactions accessible to rural patients while preserving institutional confidence.
- **Body (`Work Sans`):** Provides solid, open letterforms that remain crisp on low-resolution outdoor kiosks, thermal printouts, and doctor workstation monitors.
- **Data & Metric Labels (`JetBrains Mono`):** Dedicated to critical numerical metrics (blood pressure, pulse, SpO2, Ayurvedic Dosha ratios, and ABHA ID numbers) to eliminate ambiguity between numbers and glyphs.
- **Accessibility Guidelines:** Body font sizes must not scale below 14px on any device. For kiosk terminals, the base readable scale shifts upward to `body-lg` (18px) to accommodate varied patient standing distances.

## Layout & Spacing

The layout is built on an accessible 8pt spatial grid designed for rapid data input and touch kiosks:

- **Touch Surface Requirements:** In compliance with public healthcare terminal accessibility standards, all primary interactive kiosk targets must measure at least 64px (`4rem` / `kiosk-touch-target`). Mobile and desktop sub-actions maintain a minimum touch target of 56px (`3.5rem`).
- **Screen Adaptive Rules:**
  - **Kiosk / Desktop (12-column grid):** 32px gutters and 48px outer margins. The doctor case-entry screen is split into a 4-column persistent patient diagnostic overview and an 8-column structured case-taking workspace.
  - **Tablet OPD Station (8-column grid):** 24px gutters and 32px margins. Uses collapsable split sheets for simultaneous vitals capture and AYUSH clinical assessment.
  - **Patient Mobile / Handheld Scanner (4-column grid):** 16px gutters and 16px margins. Employs stacked full-width touch cards with persistent bottom action bars.
- **Reflow Architecture:** Content never relies on horizontal scrollbars. If data density demands overflow, cards transition to accordion tabs or pagination steps with unambiguous progress indicators.

## Elevation & Depth

This design system uses crisp, low-contrast structural boundaries with subtle tinted ambient shadows to deliver clean separation without overwhelming the user:

- **Base Tiers (Flat to Subtle Lift):**
  - *Tier 0 (Surface Base):* Soft tint (`#F8FAFC`). No elevation.
  - *Tier 1 (Card & Module Canvas):* `#FFFFFF` with a 1px solid border in `#E2E8F0` and an ambient shadow: `0 1px 3px rgba(13, 92, 70, 0.04), 0 1px 2px rgba(15, 23, 42, 0.06)`.
  - *Tier 2 (Selected State & Flyouts):* `#FFFFFF` with an active emerald border (`#0D5C46`) and shadow: `0 4px 6px -1px rgba(13, 92, 70, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.05)`.
  - *Tier 3 (Modals, Prescription Drawers & Emergency Overlays):* `#FFFFFF` framed by a 1.5px border (`#0F766E`) with heavy ambient diffusion: `0 20px 25px -5px rgba(15, 23, 42, 0.12), 0 8px 10px -6px rgba(13, 92, 70, 0.08)`.
- **High-Ambient Anti-Glare Optimization:** When deployed on kiosk hardware, shadows automatically reduce and borders increase to 2px high-contrast strokes (`#CBD5E1`) to maintain clear spatial division under harsh clinic fluorescent lighting.

## Shapes

The shape system utilizes a balanced Level 2 (`roundedness: 2`) curvature paradigm:

- **Base Radii (`0.5rem` / 8px):** Standard for form inputs, vitals metric badges, table cell containers, and secondary action chips.
- **Large Structural Radii (`1rem` / 16px):** Standard for clinical record cards, diagnostic panels, OPD queue modules, and prescription containers.
- **Extra-Large Radii (`1.5rem` / 24px):** Reserved for modal sheets, patient profile summary headers, and kiosk welcome panels.
- **Pill Geometry (`9999px`):** Reserved exclusively for status indicators (e.g., "Normal", "Critical", "Prakriti: Vata-Pitta") and primary icon buttons to signal their non-editable, categorical nature.

## Components

### Buttons
- **Primary Clinical Action:** Background `#0D5C46`, text `#FFFFFF`, 16px medium/semi-bold. Minimum height of 56px (64px on kiosk). Hover state `#0A4736`, active state `#073327`. Focus ring is 3px solid with a 2px offset in `#0F766E`.
- **Secondary Action:** Transparent background with a 1.5px solid border in `#0F766E`, text `#0F766E`. On hover, background shifts to `#F0FDFA`.
- **Urgent / Emergency AYUSH Override:** Background `#D97706`, text `#FFFFFF`. Hover state `#B45309`. Focus ring in `#FBBF24`.

### Input Fields & Search Bars
- Background `#FFFFFF` surrounded by a 1.5px border in `#CBD5E1`. Height is 56px.
- Internal padding: 16px horizontal. Active focus shifts the border to 2px solid `#0D5C46` with a soft emerald glow (`rgba(13, 92, 70, 0.12)`).
- Helper and error text are always accompanied by an unambiguous iconography signifier (e.g., checkmark, warning circle).

### Cards & Case Containers
- White background (`#FFFFFF`), 16px border radius, 1px border in `#E2E8F0`. 
- Clinical section headers feature a 4px left-edge accent line in `#0D5C46` (Ayurvedic/General notes) or `#0F766E` (Diagnostics/Vitals).
- Internal card padding defaults to 24px (`space-lg`), reducing to 16px (`space-md`) on mobile screens.

### High-Touch Status Badges & Critical Alerts
- Pill-shaped (`rounded-full`), minimum padding 6px vertical by 14px horizontal.
- **Normal Range / Balanced Dosha:** Background `#DCFCE7`, text `#166534`, border 1px solid `#BBF7D0`.
- **Abnormal / Attention Needed:** Background `#FEF3C7`, text `#92400E`, border 1px solid `#FDE68A`.
- **Critical / Contraindicated Alert:** Background `#FEE2E2`, text `#991B1B`, border 1px solid `#FECACA`, featuring a pulsating high-contrast dot.

### Medication & Prescription Cards
- Designed for quick reading by both pharmacists and patients. Features a bold medicine title (Ayurvedic classical formulation or generic drug), JetBrains Mono dosage schedule (`1-0-1 After Food`), administration path badge, and duration block.
- Color-coded border ribbons indicate AYUSH dispensary categories (e.g., Kashayam, Vati, Churna, Taila).

### Checkboxes & Radio Buttons
- Sized at a touch-friendly 24x24px within an expanded 48x48px hit target.
- Selected state uses `#0D5C46` with a high-contrast white glyph. Radio elements use a solid inner circle with a 3px white gap buffer for distinct visual feedback.