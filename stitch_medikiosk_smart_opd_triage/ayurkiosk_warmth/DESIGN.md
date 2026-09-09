---
name: AyurKiosk Warmth
colors:
  surface: '#e7fff2'
  surface-dim: '#c8dfd3'
  surface-bright: '#e7fff2'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#e1f9ec'
  surface-container: '#dcf3e7'
  surface-container-high: '#d6eee1'
  surface-container-highest: '#d0e8dc'
  on-surface: '#0b1f18'
  on-surface-variant: '#3f4944'
  inverse-surface: '#20342c'
  inverse-on-surface: '#dff6ea'
  outline: '#6f7974'
  outline-variant: '#bfc9c2'
  surface-tint: '#1d6a51'
  primary: '#00523c'
  on-primary: '#ffffff'
  primary-container: '#1e6b52'
  on-primary-container: '#9ee9c9'
  inverse-primary: '#8cd5b7'
  secondary: '#904d00'
  on-secondary: '#ffffff'
  secondary-container: '#fe932c'
  on-secondary-container: '#663500'
  tertiary: '#00513b'
  on-tertiary: '#ffffff'
  tertiary-container: '#006c4f'
  on-tertiary-container: '#8eebc4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#a7f2d2'
  primary-fixed-dim: '#8cd5b7'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#ffdcc3'
  secondary-fixed-dim: '#ffb77d'
  on-secondary-fixed: '#2f1500'
  on-secondary-fixed-variant: '#6e3900'
  tertiary-fixed: '#98f5ce'
  tertiary-fixed-dim: '#7bd8b2'
  on-tertiary-fixed: '#002116'
  on-tertiary-fixed-variant: '#00513b'
  background: '#e7fff2'
  on-background: '#0b1f18'
  surface-variant: '#d0e8dc'
typography:
  display-kiosk:
    fontFamily: Plus Jakarta Sans
    fontSize: 44px
    fontWeight: '700'
    lineHeight: 56px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 34px
    fontWeight: '700'
    lineHeight: 44px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
  body-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 30px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
  audio-callout:
    fontFamily: Plus Jakarta Sans
    fontSize: 17px
    fontWeight: '600'
    lineHeight: 24px
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  touch-min: 3.5rem
  touch-comfortable: 4rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  space-3xl: 4rem
  gutter-kiosk: 2rem
  margin-kiosk: 2.5rem
---

## Brand & Style
The design system is crafted specifically for outpatient department (OPD) kiosks and assisted healthcare touchscreens across diverse demographics, with primary empathy directed toward senior citizens, multi-generational caregivers, and individuals with lower digital literacy. The brand personality embodies deep therapeutic reassurance, calm dignity, accessibility, and rooted Ayurvedic/AYUSH warmth.

The visual style merges **Warm Modernism** with **Gentle Tactile Accessibility**:
- **Dignified & Welcoming:** No clinical coldness or stark utilitarian hospital whites. The interface feels like a calm, sunlit wellness pavilion.
- **Low Cognitive Load:** Single-objective screens, persistent audio assists, uncrowded layouts, and obvious physical affordances.
- **Visual Clarity without Harshness:** Extreme high-contrast typography rendered in deep forest charcoal instead of sterile pitch black, paired with organic botanical sage and golden turmeric accents.

## Colors
The color palette establishes an environment of natural healing, clarity, and safety. Every tone is selected to exceed WCAG 2.1 AAA contrast benchmarks for senior visual comfort while eliminating harsh digital glare.

- **Primary Forest Sage (`#1E6B52`)**: Anchors critical navigation, primary actions, and confirmation states. Yields an 8.2:1 contrast ratio against cream canvas.
- **Secondary Amber Marigold (`#D97706`)**: Represents holistic vitality; highlights current steps, status notices, and attention-worthy instructions without inducing panic.
- **Tertiary Botanical Mint (`#2A8C6B`)**: Used for supportive indicators, badges, and progress tracks.
- **Neutral Deep Forest Charcoal (`#1A2E26`)**: The primary text color. Soft on aging eyes while preserving maximum crispness.
- **Sub-Neutral Slate (`#3E5249`)**: For secondary explanatory text and field labels.
- **Surface Canvas (`#FCFBF7`)**: A soothing warm linen background that avoids the eye-strain of raw `#FFFFFF`.
- **Card Fill (`#F3F9F6`)**: Gentle mint-tinted warm white that organizes content into clear spatial zones.
- **Warm Accent Base (`#FFF9E6`)**: Container color for audio guides, important notices, and doctor consultation tickets.
- **Border Subtle (`#D4E5DD`)**: Soft organic boundary to distinguish cards without sharp visual division.

## Typography
**Plus Jakarta Sans** is employed across all hierarchy tiers. Its wide aperture, rounded terminals, tall x-height, and open letter counters prevent optical blurring for presbyopic seniors and cataract-affected vision.

### Typographic Principles:
- **Baseline Scale:** Text never drops below 15px anywhere in the product. Primary instructional body copy is locked at `body-xl` (20px) or `body-lg` (18px).
- **Multilingual Accommodation:** Line heights are padded by an additional 15–20% compared to standard SaaS systems to accommodate Indic script ligatures and diacritics (Devanagari, Tamil, Telugu, Bangla) when toggled into vernacular audio/text modes.
- **Hierarchy Restraint:** Never stack more than two typography weights per view. Large structural titles allow immediate screen orientation at a distance of 1 meter (standing kiosk usage).

## Layout & Spacing
The layout model employs a bounded, distraction-free grid optimized for large portrait or landscape touchscreen kiosks and assisted tablet formats.

- **Primary Target Rule:** No interactive element (button, slot card, selector, icon toggle) can be under 56px (`3.5rem`) in height or width. The standard recommendation is 64px (`4rem`).
- **Grip & Reach Margins:** Kiosk interfaces feature fixed side margins of at least 40px (`2.5rem`) to keep buttons away from the extreme physical bezel of the hardware enclosure.
- **Vertical Stack Structure:** 
  1. **Top Anchor (Persistent):** Emergency assistance trigger, High-Contrast switch, and Regional Language/Audio switcher.
  2. **Active Step Context:** Single question or operational prompt in bold display typography accompanied by a "Speak/Suno" audio prompt.
  3. **Interaction Area:** 1 to 4 large selectable cards or wide input surfaces.
  4. **Bottom Anchor (Fixed):** Green "Aage Badhein / Next" primary action alongside a clear "Peeche / Go Back" anchor.

## Elevation & Depth
Depth is created through gentle organic warmth rather than synthetic grey shadows.

- **Surface Tiers:**
  - Base: Canvas `#FCFBF7`.
  - Tier 1 (Cards, Selectors): `#F3F9F6` with an inner or outline border of 1.5px `#D4E5DD`.
  - Tier 2 (Highlighted Selections & Audio Banners): `#FFF9E6` with a warm amber outline `#FDE68A`.
- **Soft Ambient Shadows:** Elements utilize diffused herbal shadows: `0 8px 24px -4px rgba(30, 107, 82, 0.08), 0 2px 6px -1px rgba(26, 46, 38, 0.04)`.
- **Active Physical Feedback:** On touch/press, cards depress slightly with reduced blur and an amplified 3px border in `#1E6B52`, confirming physical registration for arthritic or uncertain fingers.

## Shapes
The shape language uses high roundedness (`roundedness: 3`, pill and generous bubble geometry) to soften the healthcare environment and remove the anxiety of institutional medical machines.

- **Buttons & Chips:** Fully pill-shaped (`rounded-full`, 9999px) for single line commands to reinforce their clickable, friendly nature.
- **Information & Department Cards:** Curved using large radii (`rounded-2xl` to `rounded-3xl`, 20px–28px) evoking natural, soft-cornered touchpoints.
- **Form Containers & Keypad Buttons:** Rounded squares with 16px corner curves to maintain structural alignment.

## Components

### 1. Buttons
- **Primary Action (Proceed / Confirm):** Height 64px, pill shape, background `#1E6B52`, text `#FFFFFF`, bold `label-lg`. Includes an elevated, high-contrast right-arrow icon in a soft circle.
- **Secondary Action (Back / Cancel):** Height 56px, background `#EAF5F0`, text `#1E6B52`, border 2px solid `#2A8C6B`.
- **Assistance Button (May I Help You?):** Prominent pill button styled in `#FFF9E6`, border 2px solid `#D97706`, text `#B45309`, paired with a live representative/headset icon.

### 2. Audio Speaker Badge ("Awaaz / Suno")
- Prominent floating or inline pill attached to primary questions and instructions.
- Styled in light amber `#FEF3C7` with a glowing speaker icon, text "Audio Sahayata" (Listen to this screen), pulsing subtly to invite users who cannot read the displayed text.

### 3. Selection Cards (Doctor, Department, Token, Slot)
- Minimum height 96px.
- Unselected: Background `#F3F9F6`, 1.5px border `#D4E5DD`, large clear icons (Ayurveda, Yoga, Unani, Siddha, Homeopathy) on the left, primary text in 20px `#1A2E26`.
- Selected: Background `#FFFFFF`, 3px solid `#1E6B52`, ambient sage drop-shadow, bold checkmark pill on the top right corner.

### 4. Inputs & Numeric Keypads (Mobile / Aadhaar / ABHA ID)
- Display inputs: Large text fields (height 72px) with centered, monospace-spaced numerals at 32px font size, enclosed in `#FFFFFF` with a 2px `#1E6B52` focus outline.
- Touch Keypad: Oversized on-screen circular or rounded-rectangular keys (minimum 64px x 64px) with high-contrast digits and clear audio click haptics.

### 5. Checkboxes & Radio Selectors
- Replaced by large selectable card toggles wherever possible.
- When native radio buttons are required, diameter is locked to 32px with a 4px border and an 18px solid center dot upon selection.

### 6. Printed OPD Slip Preview (Kiosk Output)
- Rendered on a clean cream card styled like a physical token ticket with perforated edge accents, displaying token number in 48px bold font, department name, room number, and doctor name in bilingual format.