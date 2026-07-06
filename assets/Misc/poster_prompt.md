# Space Defender — Professional Poster Image Prompt
**Version:** 1.0
**Target resolution:** 3840 × 2160 (4K UHD), portrait 2:3
**Created for:** Ali Mortazavi — Kharazmi Youth Festival 1404-1405 (2025-2026)
**Persian subtitle:** بازی محافظ فضا
**Persian font policy:** B Nazanin (primary) → Nastaliq (fallback) → Sahel (last resort)
**Encoding:** UTF-8

---

## 1. Primary Prompt (long, comprehensive — use for Gemini / Flux / Ideogram)

```
Create a professional 4K (3840×2160) ultra-high-resolution cinematic
game-poster for an indie sci-fi space-shooter.

OUTPUT SPECIFICATIONS
- Exact pixel dimensions: 3840 × 2160 (4K UHD)
- Aspect ratio: 2:3 (portrait poster)
- Color depth: 16-bit, no banding, no visible compression artifacts
- File format: PNG (preferred) or high-quality JPG (≥ 92% quality)
- No watermarks, no stock-photo look, no 3D-render plastic look

TYPOGRAPHY — every line of text below MUST appear in the image,
spelled EXACTLY as written, in the EXACT position specified.
The Persian subtitle must use B Nazanin (or a high-quality
Nastaliq fallback if B Nazanin is unavailable). The Persian
characters must render correctly — no garbled glyphs, no
right-to-left flip errors, no missing diacritics.

  [Top-center, large, bold futuristic sans-serif, white with
   subtle cyan/blue neon outer glow, drop-shadow]
   "SPACE DEFENDER"

  [Directly underneath the English title, smaller (~55% of
   title height), in B Nazanin or Nastaliq, white with soft
   golden tint, right-aligned within its line]
   "بازی محافظ فضا"

  [Bottom-right corner, clean modern sans-serif, white, small]
   "Created by Ali Mortazavi"

  [Bottom-left corner, small rectangular badge with subtle
   border, sans-serif, white text on dark translucent panel]
   "Kharazmi Youth Festival 2025-2026"

  [Bottom-center, italic modern serif or condensed sans,
   white with slight glow, medium size]
   "Defend the planet. Master the skies."

MAIN SCENE — hero composition, centered
- Foreground (lower 1/3): a sleek angular sci-fi starfighter,
  facing the viewer, banking slightly upward, engines glowing
  bright cyan-white with volumetric thrust trails and motion
  blur. The ship is the visual anchor — sharp focus, strong
  rim-light on its edges.
- The starfighter is firing a salvo of glowing blue plasma
  bullets upward into the enemy wave. Tracer trails and
  lens-flare on the bullets.
- Midground (center): 12-20 menacing biomechanical alien
  enemy ships in red/orange threat colors, varied silhouettes
  (cruiser-class, drone, fighter, bomber, and ONE large
  boss-class mothership in upper-center). The boss is 3×
  larger than the fighters and slightly out of focus for
  depth.
- Background: deep navy-black starfield with thousands of
  pin-prick stars and a faint purple nebula on the right
  edge.
- Lower background: a large teal-blue Earth-like home planet
  in the lower third, partially illuminated (terminator line
  visible), with orbital defense rings, city lights glowing
  in the night side, and a thin atmospheric halo.
- Foreground debris: 2-3 small asteroid rocks for depth.
- Action details: explosion particles, lens flares, blue/red
  contrails, motion blur on bullets and enemies, subtle
  shockwave rings on the planet's surface.

VISUAL STYLE
- Professional AAA indie game art (reference mood: "Stellar
  Blade", "Starfield", "Everspace 2", or "Galaga reimagined
  in modern 4K").
- Color palette:
    Background:     deep navy (#0A0E27) → black (#000000)
    Hero/starfighter: cyan-blue (#00D4FF) with white highlights
    Enemies:         warm orange-red (#FF4500) with black accents
    Planet:          teal-blue (#2A8FB5) with golden city lights
    Accents:         pure white (#FFFFFF) for stars and bullets
- Cinematic lighting: 3-point lighting on the starfighter,
  rim-light on the edges, bloom on engines and explosions,
  shallow depth-of-field with sharp subject, atmospheric
  haze in the distance.
- Composition: rule-of-thirds, starfighter at lower-left
  intersection, boss at upper-right intersection, title
  centered top, credits anchored bottom.

NEGATIVE PROMPT (what to avoid)
- Garbled, mirrored, or missing Persian/Arabic glyphs
- Spelling errors in "SPACE DEFENDER", "بازی محافظ فضا",
  "Ali Mortazavi", or "Kharazmi Youth Festival 2025-2026"
- Watermarks, signatures, or "© 2024 AI Generator" stamps
- Stock-photo look, plastic 3D-render look, anime style,
  cartoon style, pixel art, or low-poly look
- Cluttered composition — only the specified text + scene
- English-only text, or missing any of the five text lines
- Blurry main subject, soft typography, illegible text
- More than one starfighter (it is a single-pilot scene)
- Photorealistic human faces (no pilot visible — cockpit
  is closed/dark)
- Multiple planets or competing focal points
```

---

## 2. Short Variant (for token-limited engines such as DALL·E 3)

```
Professional 4K (3840×2160, portrait 2:3) cinematic game-poster
for "SPACE DEFENDER" (top-center, bold futuristic font, white
with cyan neon glow). Persian subtitle directly below in
B Nazanin: "بازی محافظ فضا". Bottom-right credit: "Created by
Ali Mortazavi". Bottom-left badge: "Kharazmi Youth Festival
2025-2026". Bottom-center tagline: "Defend the planet. Master
the skies." A sleek sci-fi starfighter in lower-center
foreground firing glowing blue plasma at 15+ red/orange alien
enemy ships. One large boss-class mothership in upper-center.
Teal-blue Earth-like home planet in lower background with
city lights. Deep navy starfield. AAA indie-game art style,
cinematic rim-light, bloom, motion blur on bullets. No
watermarks, no garbled text, no spelling errors, no extra
text.
```

---

## 3. Engine-Specific Variants

### 3A. Gemini (Nano Banana Pro / Imagen 3)

Use the **Primary Prompt** as-is. Add the following toggles in the UI:
- Aspect ratio: **Portrait 2:3**
- Resolution: **4K (3840×2160)**
- Style: **Photorealistic / Cinematic**
- Typography mode: **ON** (forces accurate text rendering)
- Negative prompt: paste the negative-prompt block above

If a letter in the Persian text is wrong, regenerate with this
appended suffix: `, with perfectly rendered Persian Nastaliq
script, no glyph errors, correct right-to-left flow`.

### 3B. Midjourney v6

Append these parameters to the Primary Prompt:
```
--ar 2:3 --v 6 --q 2 --s 250 --style raw
```
Then issue a follow-up `/describe` or `/shorten` command if the
text renders incorrectly. For best typography, prefer
`--style raw` (less Midjourney "stylization" interference with
text). If Persian text fails, use the Short Variant — Midjourney
handles short prompts more reliably for typography.

**Alternative Midjourney trick (for guaranteed typography):**
Generate the scene WITHOUT text (use `--no text, letters,
typography, watermark`), then composite the text in Photoshop /
Canva / Figma afterward. The five text lines are short and
simple enough to overlay at 4K.

### 3C. DALL·E 3 (via ChatGPT)

Use the **Short Variant**. DALL·E 3 has a hard time with
non-Latin scripts — be prepared to:
1. Generate the scene first
2. Use ChatGPT's "edit" or "inpainting" to add the text layer
3. Or composite the text in Canva / Photoshop

**Best approach for DALL·E 3:** generate the image WITHOUT text
in the prompt, then ask ChatGPT: *"Add the following text to
the image in the specified positions: [list text + positions]"*.
DALL·E 3 is much more reliable with English than Persian, so
the Persian subtitle may still need manual overlay.

---

## 4. Color & Composition Reference

| Element | Color | Hex | Notes |
|---|---|---|---|
| Space background | Deep navy | #0A0E27 | Gradient to #000000 at edges |
| Stars | Pure white | #FFFFFF | Pin-pricks, varied opacity |
| Starfighter | Cyan-blue | #00D4FF | With white highlights |
| Plasma bullets | Cyan-white | #B0F2FF | With motion blur |
| Enemies (standard) | Orange-red | #FF4500 | With black accents |
| Boss mothership | Deep red | #B22222 | Larger, slightly out of focus |
| Planet | Teal-blue | #2A8FB5 | With golden city lights (#FFD700) |
| Title text | White | #FFFFFF | Cyan glow #00D4FF |
| Persian subtitle | Off-white | #F8F0E3 | Soft golden tint |
| Tagline | White | #FFFFFF | Subtle glow |

**Composition grid (rule of thirds):**
- Starfighter: lower-left intersection
- Boss mothership: upper-right intersection
- Earth: lower-right intersection (partially visible)
- Title: top-center (above upper-third line)
- Credits: bottom corners and bottom-center

---

## 5. Verification Checklist (check before saving)

Before saving the generated image as `poster.png`, confirm:

- [ ] Resolution is exactly 3840 × 2160 pixels (or larger at 2:3 ratio)
- [ ] All five text strings are present and readable
- [ ] "SPACE DEFENDER" has NO spelling errors
- [ ] "بازی محافظ فضا" has NO garbled, mirrored, or missing glyphs
- [ ] "Ali Mortazavi" is spelled exactly right (no "Morazavi" or similar)
- [ ] "Kharazmi Youth Festival 2025-2026" matches exactly
- [ ] "Defend the planet. Master the skies." is the tagline
- [ ] NO watermark, signature, or AI-generator stamp
- [ ] NO extra text (e.g., random words, "Sample", "Demo")
- [ ] Starfighter is sharp and well-lit (focal point)
- [ ] Boss mothership is recognizable as a single large enemy
- [ ] Color palette matches (cyan hero, red enemies, teal planet)
- [ ] No photorealistic human faces (pilot is hidden)
- [ ] Persian subtitle renders in B Nazanin or Nastaliq (not Latin glyphs)
- [ ] Image looks cinematic, not cartoonish or pixel-art
- [ ] Title text is large enough to be read from 2 meters away (poster scale)
- [ ] File size is reasonable (< 5 MB for competition upload)

---

## 6. Suggested Save Location

```
C:\Users\Reza Mortazavi\Dropbox\Projects\School\Ali\Kharazmi\Game\poster.png
```

If you regenerate iterations, save with version suffix:
- `poster_v1.png`
- `poster_v2.png`
- `poster_final.png` (the version you choose to submit)

---

## 7. Quick-Paste Summary (entire primary prompt, single block)

```
Create a professional 4K (3840×2160) ultra-high-resolution cinematic
game-poster for an indie sci-fi space-shooter. Aspect ratio 2:3
portrait. No watermarks. Title at top-center in bold futuristic
white sans-serif with cyan neon glow: "SPACE DEFENDER". Persian
subtitle directly below in B Nazanin (or Nastaliq fallback):
"بازی محافظ فضا". Bottom-right credit: "Created by Ali Mortazavi".
Bottom-left badge: "Kharazmi Youth Festival 2025-2026". Bottom-
center tagline: "Defend the planet. Master the skies." Main scene:
a sleek angular sci-fi starfighter in the lower-center foreground
firing glowing cyan-blue plasma bullets at 12-20 red/orange alien
enemy ships and one large boss-class mothership in the upper
area. A teal-blue Earth-like home planet in the lower background
with orbital rings and city lights. Deep navy starfield, lens
flares, motion blur on bullets, bloom on engines, cinematic rim-
light. AAA indie-game art style. Color palette: deep navy
background, cyan-blue hero, orange-red enemies, teal planet, white
highlights. All text must be 100% legible, spelled exactly as
written, no garbled Persian glyphs, no extra text, no stock-photo
look.
```
