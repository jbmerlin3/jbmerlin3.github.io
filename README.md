# jbmerlin3.github.io

Portfolio site for Jonathan Merlin, built with [Quarto](https://quarto.org) and
published to https://jbmerlin3.github.io by GitHub Actions on every push to `main`.

## Preview locally

Quarto ships inside RStudio, so nothing extra needs installing:

```bash
alias quarto="/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto"
```

- **While editing:** `quarto preview` opens the site and reloads on every save. It
  injects its own script into each page, and that script can stall navigation (the
  navbar's Arsenal App link sometimes takes several seconds), so do not judge links
  or speed there.
- **Before you push, review the real build** exactly as GitHub Pages will serve it:

  ```bash
  quarto render && python3 -m http.server 4322 --directory _site
  ```

  then open http://localhost:4322.

## Add a blog post

1. Make a folder `blog/YYYY-MM-DD-short-slug/`.
2. Put an `index.qmd` in it, starting from this header:

   ```yaml
   ---
   title: "Post title"
   subtitle: "One-line hook"
   author: "Jonathan Merlin"
   date: 2026-10-01
   description: "One or two sentences shown on the Blog page."
   categories: [Braves, Prospects]
   image: some-chart.png        # optional, used for link previews
   ---
   ```

3. Write the post in Markdown below the header. Drop images in the same folder
   and reference them as `![Caption](chart.png)`. A PDF version can sit next to it
   with a `[Download the PDF](file.pdf)` link.

The Blog page, the "Latest writing" list on the home page and the RSS feed pick it up
automatically.

## Add a project

Same pattern in `projects/<slug>/index.qmd`. The Projects page lists it automatically.
To also put it in the navbar's Projects menu, add one entry under `menu:` in `_quarto.yml`.
To feature it on the home page, add a card in `index.qmd`.

## Add a scouting report

1. Make `scouting/<player-name>/` and copy the PDF in.
2. Make the web images (cropped, compressed `report.jpg` and `thumb.jpg`):

   ```bash
   pip install pymupdf    # once
   python3 scripts/scouting_images.py scouting/<player-name>/<Report>.pdf
   ```

3. Copy `scouting/parker-wiles/index.qmd` and edit the header and summary. Leave out
   `date:`, since the forms are undated.

## The Arsenal app

`app.qmd` loads the live app at https://jonathanmerlin.shinyapps.io/pitcher-arsenal/,
so changes deployed to the app show up here with no site change. The app loads only
when someone clicks "Launch", so skimmers do not spend shinyapps.io free-tier hours.

To refresh the preview screenshot (`images/arsenal-app.png`) after a visual change
to the app, run `scripts/app_screenshot.py` (needs Google Chrome and the
`websocket-client` Python package):

```bash
python3 scripts/app_screenshot.py /tmp https://jonathanmerlin.shinyapps.io/pitcher-arsenal/ images/arsenal-app.png 80
```

## Link previews

`images/social-card.png` is the card LinkedIn, Slack and iMessage show when the site
link is pasted. Its source is `scripts/social-card.html`; edit it, then re-render it
at 1200x630 with headless Chrome:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --window-size=1200,630 --hide-scrollbars \
  --screenshot=images/social-card.png "file://$PWD/scripts/social-card.html"
```

A page can set its own preview with `image:` in its header, as the blog post does.

## Change the look

- Accent color: `$accent` in `theme.scss` (light) and `theme-dark.scss` (dark).
- Navbar tabs, resume, and social links: `_quarto.yml`.
- Resume: replace `files/Jonathan-Merlin-Resume.pdf` and keep the file name.
