# take.town

Personal site for Pat Dennis. Built with a custom Python static site generator.

**Live at [take.town](https://take.town)**

## Local development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python build.py
cd _site && python3 -m http.server 8000
```

## How it works

- `build.py` — Reads markdown posts from `_posts/` and pages from `pages/`, renders them through Jinja2 templates, and outputs static HTML to `_site/`.
- `site.yml` — Site configuration (title, description, author, etc.)
- `templates/` — Jinja2 HTML templates
- `assets/` — CSS and images
- Deploys to GitHub Pages via GitHub Actions on push to `main`.
