# Portfolio site: working notes for Claude

Quarto website, published to GitHub Pages by `.github/workflows/publish.yml` on push to main.
Quarto binary: `/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto` (not on PATH).

- The site is employer-facing. Jonathan reviews locally (`quarto preview`) before any commit or push.
- Content lives as one folder per item: `blog/<date-slug>/`, `projects/<slug>/`, `scouting/<player>/`,
  each with an `index.qmd`. Listing pages glob those folders, so a new item needs no other edit
  (except the navbar menu for projects, and the home-page cards, which are hand-curated).
- Converting a PDF into a page: keep his numbers and claims exactly; copy-edit only, list every
  change you make in chat, and keep the original PDF linked at the top.
- Writing style: verdict first, no em dashes, name judgment calls explicitly.
- The app page must not auto-load the Shiny iframe (free-tier active hours). Keep click-to-load.
- Pages are pure Markdown, no executed code, so CI needs only Quarto, not R.
- Stuff+ is not finished (it is the next project). Do not feature or describe a Stuff+ model in the bio,
  cards or tags until Jonathan says it is ready. The Detmers report body still uses its grades as written.
- Call the Wasserman internship "The Team" on the site.
- Scouting pages carry no date: the forms are undated, so do not guess one.
