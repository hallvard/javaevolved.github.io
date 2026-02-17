#!/usr/bin/env python3
"""Generate HTML detail pages from JSON snippet files and slug-template.html."""

import json
import glob
import os
import html
from urllib.parse import quote

BASE_URL = "https://javaevolved.github.io"

CATEGORY_DISPLAY = {
    "language": "Language",
    "collections": "Collections",
    "strings": "Strings",
    "streams": "Streams",
    "concurrency": "Concurrency",
    "io": "I/O",
    "errors": "Errors",
    "datetime": "Date/Time",
    "security": "Security",
    "tooling": "Tooling",
}


def escape(text):
    """HTML-escape text for use in attributes and content."""
    return html.escape(text, quote=True)


def json_escape(text):
    """Escape text for embedding in JSON strings inside ld+json blocks.
    
    Uses ASCII-only encoding to match the original HTML files which use
    \\uXXXX escapes for non-ASCII characters in ld+json blocks.
    """
    # json.dumps with ensure_ascii=True produces \\uXXXX for non-ASCII
    # Strip surrounding quotes since we embed in our own quoted string
    return json.dumps(text, ensure_ascii=True)[1:-1]


def load_all_snippets():
    """Load all JSON snippet files, keyed by category/slug."""
    snippets = {}
    categories = [
        "language", "collections", "strings", "streams", "concurrency",
        "io", "errors", "datetime", "security", "tooling",
    ]
    json_files = []
    for cat in categories:
        json_files.extend(sorted(glob.glob(f"{cat}/*.json")))
    for path in json_files:
        with open(path) as f:
            data = json.load(f)
        key = f"{data['category']}/{data['slug']}"
        data["_path"] = key
        snippets[key] = data
    return snippets


def render_nav_arrows(data):
    """Render prev/next navigation arrows."""
    parts = []
    if data.get("prev"):
        parts.append(
            f'<a href="/{data["prev"]}.html" aria-label="Previous pattern">←</a>'
        )
    else:
        parts.append('<span class="nav-arrow-disabled">←</span>')
    if data.get("next"):
        parts.append(
            f'<a href="/{data["next"]}.html" aria-label="Next pattern">→</a>'
        )
    else:
        parts.append("")
    return "\n          ".join(parts)


def render_why_cards(why_list):
    """Render the 3 why-modern-wins cards."""
    cards = []
    for w in why_list:
        cards.append(
            f"""        <div class="why-card">
          <div class="why-icon">{w['icon']}</div>
          <h3>{escape(w['title'])}</h3>
          <p>{escape(w['desc'])}</p>
        </div>"""
        )
    return "\n".join(cards)


def render_related_card(related_data):
    """Render a single related pattern tip-card."""
    cat = related_data["category"]
    slug = related_data["slug"]
    cat_display = CATEGORY_DISPLAY[cat]
    path = f"{cat}/{slug}"

    return f"""        <a href="/{path}.html" class="tip-card">
          <div class="tip-card-body">
            <div class="tip-card-header">
              <div class="tip-badges">
                <span class="badge {cat}">{cat_display}</span>
                <span class="badge {related_data['difficulty']}">{related_data['difficulty']}</span>
              </div>
            </div>
            <h3>{escape(related_data['title'])}</h3>
          </div>
          <div class="card-code">
            <div class="card-code-layer old-layer">
              <div class="mini-label">{escape(related_data['oldLabel'])}</div>
              <pre class="code-text">{escape(related_data['oldCode'])}</pre>
            </div>
            <div class="card-code-layer modern-layer">
              <div class="mini-label">{escape(related_data['modernLabel'])}</div>
              <pre class="code-text">{escape(related_data['modernCode'])}</pre>
            </div>
            <span class="hover-hint">Hover to see modern ➜</span>
          </div>
          <div class="tip-card-footer">
            <span class="browser-support"><span class="dot"></span>JDK {related_data['jdkVersion']}+</span>
            <span class="arrow-link">→</span>
          </div>
        </a>"""


def render_related_section(related_paths, all_snippets):
    """Render all related pattern cards."""
    cards = []
    for path in related_paths:
        if path in all_snippets:
            cards.append(render_related_card(all_snippets[path]))
    return "\n".join(cards)


def render_social_share(slug, title):
    """Render social share URLs using the old flat URL format."""
    page_url = f"{BASE_URL}/{slug}.html"
    share_text = f"{title} \u2013 java.evolved"

    encoded_url = quote(page_url, safe="")
    encoded_text = quote(share_text, safe="")

    x_url = f"https://x.com/intent/tweet?url={encoded_url}&text={encoded_text}"
    bsky_url = f"https://bsky.app/intent/compose?text={encoded_text}%20{encoded_url}"
    li_url = f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}"
    reddit_url = (
        f"https://www.reddit.com/submit?url={encoded_url}&title={encoded_text}"
    )

    return f"""  <div class="social-share">
    <span class="share-label">Share</span>
    <a href="{x_url}" target="_blank" rel="noopener" class="share-btn share-x" aria-label="Share on X">𝕏</a>
    <a href="{bsky_url}" target="_blank" rel="noopener" class="share-btn share-bsky" aria-label="Share on Bluesky">🦋</a>
    <a href="{li_url}" target="_blank" rel="noopener" class="share-btn share-li" aria-label="Share on LinkedIn">in</a>
    <a href="{reddit_url}" target="_blank" rel="noopener" class="share-btn share-reddit" aria-label="Share on Reddit">⬡</a>
  </div>"""


def generate_html(data, all_snippets):
    """Generate the full HTML page for a snippet."""
    cat = data["category"]
    slug = data["slug"]
    cat_display = CATEGORY_DISPLAY[cat]
    flat_url = f"{BASE_URL}/{slug}.html"
    cat_url = f"{BASE_URL}/{cat}/{slug}.html"

    nav_arrows = render_nav_arrows(data)
    why_cards = render_why_cards(data["whyModernWins"])
    related_cards = render_related_section(data.get("related", []), all_snippets)
    social_share = render_social_share(slug, data["title"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(data['title'])} | java.evolved</title>
  <meta name="description" content="{escape(data['summary'])}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{cat_url}">
  <link rel="stylesheet" href="../styles.css">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="manifest" href="../manifest.json">
  <meta name="theme-color" content="#f97316">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="java.evolved">

  <meta property="og:title" content="{escape(data['title'])} | java.evolved">
  <meta property="og:description" content="{escape(data['summary'])}">
  <meta property="og:url" content="{cat_url}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="java.evolved">
  <meta property="og:locale" content="en_US">
  <meta property="og:image" content="{BASE_URL}/images/social-card.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:type" content="image/png">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(data['title'])} | java.evolved">
  <meta name="twitter:description" content="{escape(data['summary'])}">
  <meta name="twitter:image" content="{BASE_URL}/images/social-card.png">

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "TechArticle",
    "headline": "{json_escape(data['title'])}",
    "description": "{json_escape(data['summary'])}",
    "url": "{flat_url}",
    "publisher": {{
        "@type": "Organization",
        "name": "java.evolved",
        "url": "{BASE_URL}"
    }},
    "mainEntityOfPage": {{
        "@type": "WebPage",
        "@id": "{flat_url}"
    }}
}}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {{
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": "{BASE_URL}/"
        }},
        {{
            "@type": "ListItem",
            "position": 2,
            "name": "{json_escape(cat_display)}",
            "item": "{BASE_URL}/?cat={cat}"
        }},
        {{
            "@type": "ListItem",
            "position": 3,
            "name": "{json_escape(data['title'])}"
        }}
    ]
}}
  </script>
</head>
<body data-page="single">
  <nav>
    <div class="nav-inner">
      <a href="/" class="logo">java.<span>evolved</span></a>
      <div class="nav-right">
        <a href="https://github.com/javaevolved/javaevolved.github.io" target="_blank" rel="noopener" class="github-link" aria-label="View on GitHub">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <circle cx="10" cy="10" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 3C6.13 3 3 6.13 3 10c0 3.09 2 5.71 4.77 6.63.35.06.48-.15.48-.33v-1.16c-1.95.42-2.36-1.07-2.36-1.07-.32-.81-.78-1.03-.78-1.03-.64-.43.05-.42.05-.42.7.05 1.07.72 1.07.72.63 1.08 1.65.77 2.05.59.06-.46.24-.77.44-.95-1.57-.18-3.22-.78-3.22-3.48 0-.77.27-1.4.72-1.89-.07-.18-.31-.9.07-1.87 0 0 .59-.19 1.93.72.56-.16 1.16-.24 1.76-.24s1.2.08 1.76.24c1.34-.91 1.93-.72 1.93-.72.38.97.14 1.69.07 1.87.45.49.72 1.12.72 1.89 0 2.71-1.65 3.3-3.23 3.47.25.22.48.65.48 1.31v1.94c0 .19.13.4.48.33C15 15.71 17 13.09 17 10c0-3.87-3.13-7-7-7z"/>
          </svg>
        </a>
        <a href="/" class="back-link">← All patterns</a>
        
        <div class="nav-arrows">
          {nav_arrows}
        </div>
      </div>
    </div>
  </nav>

  <article class="article">
    <div class="breadcrumb">
      <a href="/">Home</a>
      <span class="sep">/</span>
      <a href="/?cat={cat}">{cat_display}</a>
      <span class="sep">/</span>
      <span>{escape(data['title'])}</span>
    </div>

    <div class="tip-header">
      <div class="tip-meta">
        <span class="badge {cat}">{cat_display}</span>
        <span class="badge {data['difficulty']}">{data['difficulty']}</span>
      </div>
      <h1>{escape(data['title'])}</h1>
      <p>{escape(data['summary'])}</p>
    </div>

    <section class="compare-section">
      <div class="section-label">Code Comparison</div>
      <div class="compare-container">
        <div class="compare-panel old-panel">
          <div class="compare-panel-header">
            <span class="compare-tag old">✕ {escape(data['oldLabel'])}</span>
            <button class="copy-btn" data-code="old">Copy</button>
          </div>
          <div class="compare-code">
            <pre class="code-text">{escape(data['oldCode'])}</pre>
          </div>
        </div>
        <div class="compare-panel modern-panel">
          <div class="compare-panel-header">
            <span class="compare-tag modern">✓ {escape(data['modernLabel'])}</span>
            <button class="copy-btn" data-code="modern">Copy</button>
          </div>
          <div class="compare-code">
            <pre class="code-text">{escape(data['modernCode'])}</pre>
          </div>
        </div>
      </div>
    </section>

    <section class="why-section">
      <div class="section-label">Why the modern way wins</div>
      <div class="why-grid">
{why_cards}
      </div>
    </section>

    <div class="info-grid">
      <div class="info-card">
        <div class="info-label">Old Approach</div>
        <div class="info-value red">{escape(data['oldApproach'])}</div>
      </div>
      <div class="info-card">
        <div class="info-label">Modern Approach</div>
        <div class="info-value green">{escape(data['modernApproach'])}</div>
      </div>
      <div class="info-card">
        <div class="info-label">Since JDK</div>
        <div class="info-value accent">{data['jdkVersion']}</div>
      </div>
      <div class="info-card">
        <div class="info-label">Difficulty</div>
        <div class="info-value blue">{data['difficulty']}</div>
      </div>
    </div>

    <section class="bs-section">
      <div class="section-label">JDK Support</div>
      <div class="bs-card">
        <div class="bs-feature-name">{escape(data['title'])}</div>
        <span class="baseline-badge widely">Available</span>
        <p class="bs-desc">{escape(data['support'])}</p>
      </div>
    </section>

    <section class="explanation">
      <h2>How it works</h2>
      <p>{escape(data['explanation'])}</p>
    </section>

    <section class="related">
      <h2>Related patterns</h2>
      <div class="related-grid">
{related_cards}
      </div>
    </section>
  </article>
</section>


{social_share}

  <footer>
    <p>A project by <a href="https://github.com/brunoborges" target="_blank" rel="noopener">Bruno Borges</a></p>
    <p><a href="https://github.com/javaevolved/javaevolved.github.io" target="_blank" rel="noopener">View on GitHub</a></p>
  </footer>

  <script src="../app.js"></script>
</body>
</html>
"""


def main():
    all_snippets = load_all_snippets()
    print(f"Loaded {len(all_snippets)} snippets")

    for key, data in all_snippets.items():
        html_content = generate_html(data, all_snippets).strip()
        out_path = f"{data['category']}/{data['slug']}.html"
        with open(out_path, "w", newline="") as f:
            f.write(html_content)

    print(f"Generated {len(all_snippets)} HTML files")

    # Rebuild data/snippets.json from individual JSON files
    # This file is used at runtime by app.js for search
    snippets_list = []
    for key, data in all_snippets.items():
        # Exclude internal fields and navigation-only fields
        entry = {k: v for k, v in data.items() if k not in ("_path", "prev", "next", "related")}
        snippets_list.append(entry)

    os.makedirs("data", exist_ok=True)
    with open("data/snippets.json", "w") as f:
        json.dump(snippets_list, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Rebuilt data/snippets.json with {len(snippets_list)} entries")


if __name__ == "__main__":
    main()
