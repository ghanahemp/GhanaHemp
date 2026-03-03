"""
GhanaHemp.com Auto-Publisher Bot
=================================
Runs daily, finds real Ghana cannabis news, writes a full article
in GhanaHemp.com style, and publishes it live to your site via GitHub.

SETUP: Replace the 4 values in the CONFIG section below with your own keys.
"""

import os
import json
import base64
import datetime
import requests
import anthropic
import time

# ─────────────────────────────────────────
# CONFIG — REPLACE THESE WITH YOUR VALUES
# ─────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_SK_ANT_KEY_HERE")
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "YOUR_GHP_TOKEN_HERE")
GITHUB_USERNAME   = "ghanahemp"
GITHUB_REPO       = "GhanaHemp"
# ─────────────────────────────────────────

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SOURCES = [
    # Ghana Government & Official
    "https://www.ncc.gov.gh/news/",
    "https://www.mint.gov.gh/category/latest-news/",
    "https://cannacham.org/",
    # Ghana News
    "https://www.ghanaweb.com/GhanaHomePage/NewsArchive/cannabis",
    "https://www.graphic.com.gh/search?q=cannabis+hemp+ghana",
    "https://www.newsghana.com.gh/?s=cannabis",
    "https://www.modernghana.com/search/?q=cannabis+hemp",
    "https://www.myjoyonline.com/?s=cannabis+hemp+ghana",
    "https://citinewsroom.com/?s=cannabis+hemp",
    "https://3news.com/?s=cannabis",
    # Africa & International Cannabis
    "https://www.theafricareport.com/?s=cannabis+ghana",
    "https://internationalcbc.com/blog/",
    "https://cedclinic.com/category/news/",
    "https://www.bbc.com/pidgin/topics/c404v4ekv5et",
    "https://africacannabis.org/",
    # Global Cannabis Business
    "https://mjbizdaily.com/tag/africa/",
    "https://cannabisindustryjournal.com/",
    "https://hempindustrydaily.com/",
]

SITE_STYLE = """
You are the editorial voice of GhanaHemp.com — Ghana's leading independent hemp and cannabis news authority.

WRITING STYLE:
- Professional, factual, authoritative — like a serious Ghanaian news publication
- Always cite real sources (NACOC, mint.gov.gh, cannacham.org, GhanaWeb, Graphic Online etc.)
- Never invent quotes — only use verified statements from officials
- Always remind readers: recreational cannabis remains illegal in Ghana
- Always reference NACOC licensing where relevant: portal.ncc.gov.gh
- Tone: serious news outlet, not a blog. Think Graphic Online meets Bloomberg cannabis desk.
- Ghana-first perspective — always explain relevance to Ghanaian readers, farmers, investors

LEGAL REMINDER TO ALWAYS INCLUDE:
- Recreational cannabis is illegal in Ghana
- THC limit is 0.3% under L.I. 2475
- Apply for licences only at portal.ncc.gov.gh
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — GhanaHemp.com</title>
<meta name="description" content="{meta_desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--red:#CE1126;--gold:#FCD116;--green:#006B3F;--black:#0D0D0D;--cream:#FAF8F3;--warm:#F2EDE3;--border:#E2DDD3;--text:#1C1A17;--muted:#6B6660;}}
*{{margin:0;padding:0;box-sizing:border-box;}}body{{font-family:'IBM Plex Sans',sans-serif;background:var(--cream);color:var(--text);}}
.wrap{{max-width:800px;margin:0 auto;padding:0 32px;}}
.flag{{display:flex;height:5px;}}.fr{{flex:1;background:#CE1126;}}.fg{{flex:1;background:#FCD116;}}.fgr{{flex:1;background:#006B3F;}}
.topbar{{background:#0D0D0D;color:rgba(255,255,255,.45);font-family:'IBM Plex Mono',monospace;font-size:10px;padding:7px 32px;display:flex;justify-content:space-between;}}
.topbar a{{color:rgba(255,255,255,.4);text-decoration:none;margin-left:16px;}}
.masthead{{background:var(--cream);border-bottom:2px solid #0D0D0D;padding:18px 32px;display:flex;align-items:center;gap:16px;}}
.sn{{font-family:'Libre Baskerville',serif;font-size:32px;font-weight:700;letter-spacing:-1px;color:#0D0D0D;text-decoration:none;}}
.sn span{{color:#006B3F;}}
nav{{background:#0D0D0D;display:flex;padding:0 32px;overflow-x:auto;}}
nav a{{color:rgba(255,255,255,.68);text-decoration:none;font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.11em;text-transform:uppercase;padding:13px;border-bottom:3px solid transparent;white-space:nowrap;}}
nav a:hover{{color:#FCD116;border-bottom-color:#FCD116;}}
nav a.cta{{background:#006B3F;color:#fff;margin-left:auto;border-bottom:none!important;}}
.article-hero{{background:#0D0D0D;padding:52px 32px;position:relative;overflow:hidden;}}
.article-hero::before{{content:'';position:absolute;inset:0;opacity:.04;
  background-image:repeating-linear-gradient(0deg,#FCD116 0,#FCD116 1px,transparent 1px,transparent 44px),
  repeating-linear-gradient(90deg,#FCD116 0,#FCD116 1px,transparent 1px,transparent 44px);}}
.eyebrow{{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:#FCD116;margin-bottom:14px;display:flex;align-items:center;gap:10px;}}
.eyebrow::before{{content:'';width:24px;height:2px;background:#FCD116;}}
.article-hero h1{{font-family:'Libre Baskerville',serif;font-size:42px;font-weight:700;color:#fff;line-height:1.12;letter-spacing:-.6px;margin-bottom:16px;position:relative;z-index:1;}}
.byline{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:rgba(255,255,255,.4);position:relative;z-index:1;}}
.article-body{{padding:48px 0 80px;}}
.article-body p{{font-size:16px;line-height:1.8;color:var(--text);margin-bottom:22px;}}
.article-body h2{{font-family:'Libre Baskerville',serif;font-size:26px;font-weight:700;margin:40px 0 16px;line-height:1.2;}}
.article-body h3{{font-family:'Libre Baskerville',serif;font-size:20px;font-weight:700;margin:32px 0 12px;}}
.article-body blockquote{{border-left:3px solid #FCD116;padding:16px 20px;margin:28px 0;background:#fff;}}
.article-body blockquote p{{font-style:italic;font-size:15px;margin-bottom:4px;}}
.article-body blockquote cite{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--muted);font-style:normal;}}
.legal-box{{background:#fff8f8;border-left:4px solid #CE1126;padding:18px 20px;margin:32px 0;}}
.legal-box .lt{{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.17em;text-transform:uppercase;color:#CE1126;margin-bottom:6px;}}
.legal-box p{{font-size:13px;color:var(--muted);line-height:1.62;margin-bottom:0;}}
.source-box{{background:var(--warm);border:1px solid var(--border);padding:16px 20px;margin:32px 0;font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--muted);line-height:1.8;}}
.source-box a{{color:#006B3F;text-decoration:none;}}
.related{{border-top:2px solid #0D0D0D;padding-top:32px;margin-top:48px;}}
.related h4{{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;margin-bottom:16px;}}
.related a{{display:block;font-family:'Libre Baskerville',serif;font-size:16px;font-weight:700;color:var(--text);text-decoration:none;padding:12px 0;border-bottom:1px solid var(--border);transition:color .2s;}}
.related a:hover{{color:#006B3F;}}
footer{{background:#0D0D0D;color:rgba(255,255,255,.4);padding:32px;font-family:'IBM Plex Mono',monospace;font-size:9px;text-align:center;line-height:1.8;}}
footer a{{color:rgba(255,255,255,.3);text-decoration:none;margin:0 8px;}}
@media(max-width:600px){{.article-hero h1{{font-size:28px;}}.wrap{{padding:0 20px;}}}}
</style>
</head>
<body>
<div class="flag"><div class="fr"></div><div class="fg"></div><div class="fgr"></div></div>
<div class="topbar">
  <span>● NACOC Licensing Portal Open — portal.ncc.gov.gh · Toll-Free: 0800 307 307</span>
  <div><a href="index.html">Home</a><a href="ghana-news.html">Ghana News</a><a href="licensing.html">Licensing</a></div>
</div>
<div class="masthead">
  <a href="index.html" class="sn">Ghana<span>Hemp</span>.com</a>
</div>
<nav>
  <a href="index.html">Home</a>
  <a href="ghana-news.html">Ghana News</a>
  <a href="licensing.html">Licensing</a>
  <a href="business.html">Business</a>
  <a href="policy.html">Policy</a>
  <a href="africa.html">Africa</a>
  <a href="world.html">World</a>
  <a href="education.html">Education</a>
  <a href="resources.html">Resources</a>
  <a href="index.html#newsletter" class="cta">Newsletter →</a>
</nav>

<div class="article-hero">
  <div class="wrap">
    <div class="eyebrow">{category} — {date}</div>
    <h1>{title}</h1>
    <div class="byline">GhanaHemp.com Editorial &nbsp;·&nbsp; {date} &nbsp;·&nbsp; {read_time} min read</div>
  </div>
</div>

<div class="article-body">
  <div class="wrap">
    {body_html}
    <div class="source-box">
      <strong>Sources:</strong> {sources}
    </div>
    <div class="legal-box">
      <div class="lt">⚠ Legal Reminder</div>
      <p>Recreational cannabis remains strictly illegal in Ghana. This article covers the legal industrial hemp and medicinal cannabis sector only, governed by Act 1100 (2023) and L.I. 2475 (2023). All licensed activities require a valid NACOC licence. Apply only at <a href="https://portal.ncc.gov.gh/#licences" style="color:#CE1126;">portal.ncc.gov.gh</a>. This is not legal advice.</p>
    </div>
    <div class="related">
      <h4>Related Reading</h4>
      <a href="ghana-news.html">Latest Ghana Cannabis News →</a>
      <a href="licensing.html">NACOC Licensing Guide — All 11 Categories →</a>
      <a href="policy.html">Ghana Cannabis Law — Full Legal Timeline →</a>
      <a href="business.html">Business &amp; Investment Opportunities →</a>
    </div>
  </div>
</div>

<footer>
  © 2026 GhanaHemp.com — Ghana's Independent Hemp &amp; Cannabis News Authority<br>
  Not legal or medical advice. All regulatory info sourced from ncc.gov.gh · mint.gov.gh
  <br><br>
  <a href="index.html">Home</a><a href="ghana-news.html">News</a><a href="licensing.html">Licensing</a><a href="education.html">Education</a><a href="resources.html">Resources</a>
</footer>
</body>
</html>"""


def search_for_news():
    """Use Claude to search for and identify the latest Ghana cannabis news."""
    print("🔍 Searching for latest Ghana cannabis news...")
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": """Search for the very latest Ghana cannabis, hemp, or NACOC news from the past 7 days.
            
Search these topics for very recent news (past 7 days):
1. "Ghana cannabis 2026" OR "Ghana hemp NACOC 2026"
2. "Ghana cannabis licensing" OR "NACOC cannabis"
3. "Ghana hemp programme" OR "Ghana cannabis regulatory"
4. Check these specific outlets for Ghana cannabis coverage: modernghana.com, myjoyonline.com, citinewsroom.com, theafricareport.com, internationalcbc.com, 3news.com, graphic.com.gh

Pick the single most newsworthy and recent story you find.

Return a JSON object with this exact structure:
{
  "has_news": true/false,
  "headline": "The most newsworthy headline you found",
  "summary": "2-3 sentence summary of what happened",
  "source_url": "the URL where you found this",
  "source_name": "name of the publication",
  "category": "Policy/Licensing/Business/Legal/Industry/Research",
  "date": "the date of the news"
}

Only return the JSON, nothing else."""
        }]
    )
    
    # Extract text from response
    full_text = ""
    for block in response.content:
        if hasattr(block, 'text'):
            full_text += block.text
    
    # Parse JSON
    try:
        import re
        json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
        if json_match:
            news = json.loads(json_match.group())
            print(f"✅ Found news: {news.get('headline', 'No headline')}")
            return news
    except Exception as e:
        print(f"⚠️ Could not parse news JSON: {e}")
    
    return None


def write_article(news_data):
    """Use Claude to write a full GhanaHemp-style article."""
    print("✍️  Writing article...")
    
    prompt = f"""You are GhanaHemp.com editor. Write a 500-word news article in HTML.

NEWS: {news_data.get('headline')}
SUMMARY: {news_data.get('summary')}
SOURCE: {news_data.get('source_name')}
CATEGORY: {news_data.get('category')}

Rules:
- Use only <p>, <h2>, <h3>, <blockquote><p></p><cite></cite></blockquote> tags
- 3 sections with h2 headings
- Mention NACOC, L.I. 2475, portal.ncc.gov.gh where relevant
- End with What This Means section
- Ghana-first perspective
- Return ONLY the HTML, nothing else
"""
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    article_html = response.content[0].text.strip()
    print(f"✅ Article written ({len(article_html)} chars)")
    return article_html


def generate_filename(headline):
    """Convert headline to a clean filename."""
    import re
    slug = headline.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = slug[:60]
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    return f"article-{date_str}-{slug}.html"


def build_html(news_data, article_body):
    """Assemble the full HTML page."""
    title = news_data.get('headline', 'Ghana Cannabis News')
    category = news_data.get('category', 'Ghana News')
    source_name = news_data.get('source_name', 'GhanaHemp.com')
    source_url = news_data.get('source_url', 'https://ghanahemp.com')
    date_str = datetime.datetime.now().strftime('%B %d, %Y')
    
    # Estimate read time (avg 200 words per minute)
    word_count = len(article_body.split())
    read_time = max(3, round(word_count / 200))
    
    meta_desc = news_data.get('summary', title)[:155]
    sources = f'<a href="{source_url}" target="_blank">{source_name}</a> · <a href="https://www.ncc.gov.gh/cannabis-regulations/" target="_blank">NACOC (ncc.gov.gh)</a> · <a href="https://www.mint.gov.gh/" target="_blank">Ministry of the Interior (mint.gov.gh)</a>'
    
    return HTML_TEMPLATE.format(
        title=title,
        meta_desc=meta_desc,
        category=category,
        date=date_str,
        read_time=read_time,
        body_html=article_body,
        sources=sources,
    )


def publish_to_github(filename, html_content):
    """Push the new article HTML file to GitHub."""
    print(f"📤 Publishing {filename} to GitHub...")
    
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    content_b64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    payload = {
        "message": f"🌿 New article: {filename} [{date_str}]",
        "content": content_b64,
        "branch": "main"
    }
    
    response = requests.put(url, headers=headers, json=payload)
    
    if response.status_code in (200, 201):
        print(f"✅ Published successfully!")
        file_url = f"https://ghanahemp.com/{filename}"
        print(f"🌍 Live at: {file_url}")
        return True
    else:
        print(f"❌ GitHub error {response.status_code}: {response.text}")
        return False


def update_news_page(filename, news_data):
    """Prepend the new article link to ghana-news.html on GitHub."""
    print("📰 Updating Ghana News page...")
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    # Get current ghana-news.html
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/ghana-news.html"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"⚠️ Could not fetch ghana-news.html: {response.status_code}")
        return False
    
    data = response.json()
    current_content = base64.b64decode(data['content']).decode('utf-8')
    sha = data['sha']
    
    date_str = datetime.datetime.now().strftime('%B %d, %Y')
    category = news_data.get('category', 'Ghana News')
    headline = news_data.get('headline', 'New Article')
    summary = news_data.get('summary', '')[:140] + '...'
    
    # Build new article card to inject
    new_card = f"""
  <div class="card" style="border:2px solid var(--green);">
    <div class="ct"><div class="cti tg"></div><div class="clbl lg">{category} — NEW</div></div>
    <h3><a href="{filename}" style="text-decoration:none;color:inherit;">{headline}</a></h3>
    <p>{summary}</p>
    <div class="src">GhanaHemp.com Editorial &nbsp;·&nbsp; {date_str} &nbsp;·&nbsp; <a href="{filename}">Read full article →</a></div>
  </div>
"""
    
    # Inject after the first <div class="grid g3"> in the news grid
    inject_marker = '<div class="grid g2">'
    if inject_marker in current_content:
        updated = current_content.replace(
            inject_marker,
            inject_marker + new_card,
            1  # only replace the first occurrence
        )
    else:
        print("⚠️ Could not find injection point in ghana-news.html")
        return False
    
    # Push updated file
    updated_b64 = base64.b64encode(updated.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"📰 News page updated: {date_str}",
        "content": updated_b64,
        "sha": sha,
        "branch": "main"
    }
    
    put_response = requests.put(url, headers=headers, json=payload)
    
    if put_response.status_code in (200, 201):
        print("✅ Ghana News page updated!")
        return True
    else:
        print(f"❌ Failed to update news page: {put_response.status_code}")
        return False


def run():
    print("=" * 50)
    print("🌿 GhanaHemp.com Auto-Publisher")
    print(f"⏰ Running at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Step 1: Find news
    news = search_for_news()
    
    if not news or not news.get('has_news'):
        print("📭 No significant new Ghana cannabis news found today. Bot will try again tomorrow.")
        return
    
    # Step 2: Write article
    print("⏳ Waiting 60 seconds before writing...")
    time.sleep(60)
    article_body = write_article(news)
    
    if not article_body:
        print("❌ Article writing failed.")
        return
    
    # Step 3: Build full HTML page
    full_html = build_html(news, article_body)
    
    # Step 4: Generate filename
    filename = generate_filename(news.get('headline', 'ghana-cannabis-news'))
    
    # Step 5: Publish to GitHub (triggers Netlify auto-deploy)
    published = publish_to_github(filename, full_html)
    
    if published:
        # Step 6: Update the Ghana News page
        time.sleep(2)
        update_news_page(filename, news)
        
        print("\n" + "=" * 50)
        print("✅ DONE! New article live on GhanaHemp.com")
        print(f"📄 File: {filename}")
        print(f"📰 Headline: {news.get('headline')}")
        print("=" * 50)
    else:
        print("❌ Publishing failed.")


if __name__ == "__main__":
    run()
