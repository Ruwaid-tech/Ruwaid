# Reflective Cycling Journal

A calm, static website that documents cycling routes, ride reflections, and highlighted insights for an MYP5 Design personal project. The site is hand-coded with semantic HTML, modular CSS, and a sprinkle of vanilla JavaScript to keep interactions accessible and lightweight.

## Project goals & personal learning

- **Project goal:** Provide a digital journal where the student can plan routes, log reflective entries, and evidence growth in both cycling practice and front-end design skills. *(Replace this sentence with your own goal statement.)*
- **Personal learning focus:** Practice structuring clean HTML/CSS without frameworks, experiment with responsive layouts, and apply accessibility heuristics. *(Replace with a short paragraph summarizing what you learned.)*
- **Personal interest:** Explain why cycling matters to you and how this project links to wellbeing, local community, or future ambitions. *(Swap this placeholder for your own story.)*

## File structure

```
/
├── index.html
├── routes.html
├── reflections.html
├── css/
│   └── styles.css
├── js/
│   └── app.js
├── data/
│   └── reflections.json
└── img/
    ├── coastal.svg
    ├── lake.svg
    ├── marina.svg
    ├── mural.svg
    ├── recovery.svg
    ├── ridge.svg
    ├── river.svg
    └── sunset.svg
```

## Customising the journal

1. **Update reflections:** Open `data/reflections.json` and edit or add entries. Each object includes fields for date, mood, summary, insight, optional photo, and tags. Keep the JSON valid (use commas between objects and wrap text in quotation marks).
2. **Replace photos:** Swap the accessible SVG placeholders in `img/` with your own route photos. Keep the same filenames (recommended) or update the `photo` field in the JSON to match your new files.
3. **Adjust styling:** Modify CSS variables at the top of `css/styles.css` to change the pastel palette, spacing, or typography scale.
4. **Add new routes:** Extend the `routesData` array in `js/app.js` with new route objects so they appear automatically on the Routes page.
5. **Testing helper:** In the browser console run `window.TEST()` to see the current filter state, highlight toggle, and how many reflections are loaded for documentation screenshots.

## Accessibility & sustainability highlights

- Semantic landmarks (`header`, `nav`, `main`, `footer`) with skip links enable quick keyboard navigation.
- Visual focus indicators, aria-live regions, accessible modals, and breadcrumb trails support WCAG 2.1 AA goals.
- Color tokens with sufficient contrast and `prefers-reduced-motion` checks ensure a comfortable experience for different needs.
- Lightweight assets: no frameworks, tiny placeholder images, CSS under ~15 KB, and deferred JavaScript for fast loading.
- Lazy-loading images and caching JSON keep the footprint small, aligning with sustainability targets.

## ACCESSFM evidence

| Criterion | Evidence in this product |
| --- | --- |
| **Aesthetics** | Pastel beige, blue, and sage palette; serif headings paired with sans-serif body text; rounded cards and gentle shadows for a calm tone. |
| **Customer** | Written for the student and local cyclists seeking reflective ride planning; clear nav and highlight toggle make reflection review easy. |
| **Cost** | Built with free tools (HTML/CSS/JS) and lightweight placeholders—no paid libraries or hosting requirements. |
| **Environment** | Small static files, lazy-loaded media, and no heavy scripts reduce bandwidth and energy use. |
| **Size** | Fully responsive layout from 320px mobile screens up to desktop widths using fluid typography and grid utilities. |
| **Safety** | Keyboard-friendly controls, visible focus rings, alt text guidance, and no flashing animations protect user wellbeing. |
| **Function** | Routes filter with live counts, accessible route detail dialog, reflection loader with highlights toggle, and weekly entry stats on the homepage. |

## Success criteria & testing methods

- [ ] **Contrast check:** Use tools such as [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) to verify the palette meets WCAG AA.
- [ ] **Keyboard navigation:** Tab through the site, open and close the route dialog, and capture a short video or screenshots proving focus order and skip link usage.
- [ ] **Weekly entries evidence:** Refresh the homepage, then take a screenshot of the element with `data-testid="entries-this-week"` showing the correct count (from `window.TEST().entriesThisWeek`).
- [ ] **Route filter demo:** Change the filter on Routes and record the live feedback message plus `window.TEST().routeFilter` output.
- [ ] **Highlight toggle proof:** Use the Reflections toggle and capture before/after screenshots; confirm the state via `window.TEST().highlightsOnly`.
- [ ] **Lighthouse audit:** Run Lighthouse in Chrome DevTools on each page and aim for Performance ≥ 90, Accessibility ≥ 95, Best Practices ≥ 95, SEO ≥ 90. Save the report screenshot.

## How accessibility and sustainability were addressed

- **Accessibility:** Implemented aria-live status messages for dynamic updates, ensured modal dialogs trap focus, provided skip links, and maintained consistent focus outlines across controls.
- **Sustainability:** Kept dependencies minimal, optimised layout for mobile-first delivery, and used lightweight placeholder imagery that can be replaced with compressed photos.

---

Happy riding and reflecting! Update content frequently to evidence your learning journey across the MYP design cycle.
