"""
GhanaHemp.com Auto-Publisher Bot v3 — FULL THROTTLE
=====================================================
5 CONTENT MODES running daily:

  MODE 1 — NEWS         Breaking Ghana cannabis news, rewritten in our voice
  MODE 2 — RESEARCH     Web research → original article, Ghana context always
  MODE 3 — EDUCATIONAL  How-to guides, explainers, beginner content
  MODE 4 — BLOG         Original opinion, analysis, deep-dive in our voice
  MODE 5 — SEO GUIDE    Long-form keyword-targeted evergreen content

DAILY LOGIC:
  Every run searches Google Trends for trending cannabis/hemp terms,
  checks what content has been published recently, and picks the
  best combination of modes to run today.

SETUP — set these environment variables on Railway:
  ANTHROPIC_API_KEY
  GITHUB_TOKEN
  TWITTER_API_KEY
  TWITTER_API_SECRET
  TWITTER_ACCESS_TOKEN
  TWITTER_ACCESS_TOKEN_SECRET
"""

import os, json, base64, datetime, requests, time, re, random
import anthropic
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    print("⚠️  tweepy not installed — Twitter posting disabled. Add tweepy to requirements.txt")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_KEY_HERE")
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "YOUR_TOKEN_HERE")
GITHUB_USERNAME   = "ghanahemp"
GITHUB_REPO       = "GhanaHemp"

# Twitter / X — set all 4 as environment variables on Railway
TWITTER_API_KEY             = os.environ.get("TWITTER_API_KEY", "")
TWITTER_API_SECRET          = os.environ.get("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN        = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ═══════════════════════════════════════════════════════
# CONTENT BANKS
# ═══════════════════════════════════════════════════════

EDUCATIONAL_TOPICS = [
    {"slug": "what-is-cbd",                  "title": "What Is CBD? A Complete Beginner's Guide",                               "brief": "Explain CBD (cannabidiol) from scratch: what it is, how it works in the body, where it comes from, what it does, what it doesn't do, how it differs from THC, what products exist, and whether it is legal in Ghana. Write for someone who has never heard of CBD before.", "category": "Education"},
    {"slug": "what-is-hemp",                 "title": "What Is Hemp? Everything You Need to Know",                              "brief": "Explain hemp as a plant: botanical definition, how it differs from marijuana, history of hemp in Africa and globally, what parts of the plant are used (seed, fibre, flower, root), industrial applications, nutritional value, and legal status in Ghana under L.I. 2475.", "category": "Education"},
    {"slug": "cbd-vs-thc",                   "title": "CBD vs THC — What's the Difference?",                                   "brief": "Detailed comparison of CBD and THC: molecular structure, how each affects the body, psychoactive vs non-psychoactive, medical applications of each, legal status of each in Ghana (THC illegal above 0.3%, CBD covered by licence), drug testing implications, and which one is in hemp.", "category": "Education"},
    {"slug": "what-is-the-endocannabinoid-system", "title": "The Endocannabinoid System Explained — Why Cannabis Affects the Human Body", "brief": "Explain the endocannabinoid system (ECS) in plain English: what it is, how it was discovered, the CB1 and CB2 receptors, how THC and CBD interact with these receptors differently, what the ECS regulates (pain, mood, sleep, appetite, immune function), and why this matters for understanding cannabis medicine.", "category": "Education"},
    {"slug": "hemp-seeds-nutrition",          "title": "Hemp Seeds Nutrition — Health Benefits, Uses and How to Eat Them",      "brief": "Complete guide to hemp seeds: nutritional profile (protein, omega-3, omega-6, vitamins, minerals), health benefits backed by research, how to use them in cooking (smoothies, salads, porridge, bread), how they compare to other seeds, and whether you can buy them in Ghana.", "category": "Education"},
    {"slug": "what-is-cbg",                   "title": "What Is CBG? The 'Mother Cannabinoid' Explained",                       "brief": "Explain CBG (cannabigerol): what it is, why it's called the mother cannabinoid, how CBG converts into CBD and THC as the plant matures, potential therapeutic benefits (appetite, inflammation, glaucoma, antibacterial), how CBG differs from CBD, and what the research currently shows.", "category": "Education"},
    {"slug": "cannabis-terpenes-explained",   "title": "Cannabis Terpenes Explained — What They Are and Why They Matter",       "brief": "Complete guide to cannabis terpenes: what terpenes are, how they create aroma and flavour, the entourage effect, the most common terpenes (myrcene, limonene, pinene, linalool, caryophyllene) and what each one does, how terpenes affect the experience, and how processors extract them.", "category": "Education"},
    {"slug": "how-cbd-oil-is-made",           "title": "How CBD Oil Is Made — From Hemp Plant to Bottle",                       "brief": "Step-by-step explanation of CBD oil production: growing and harvesting hemp, CO2 extraction vs ethanol extraction vs lipid infusion, winterisation, distillation, isolation vs full-spectrum vs broad-spectrum, lab testing, bottling. Explain quality indicators consumers should look for.", "category": "Education"},
    {"slug": "hemp-fabric-how-its-made",      "title": "Hemp Fabric — How Hemp Becomes Clothing and Textiles",                   "brief": "Explain the process from hemp plant to fabric: harvesting, retting (water vs dew), breaking and scutching, hackling, spinning, weaving. Cover: properties of hemp fabric vs cotton vs linen, environmental benefits, water usage comparison, durability, softness improvements, fashion industry adoption, and potential for Ghana's textile sector.", "category": "Education"},
    {"slug": "what-is-full-spectrum-cbd",     "title": "Full-Spectrum vs Broad-Spectrum vs CBD Isolate — What's the Difference?",  "brief": "Explain the three types of CBD products: full-spectrum (contains all cannabinoids including trace THC), broad-spectrum (all cannabinoids, THC removed), and CBD isolate (pure CBD only). Cover the entourage effect, which is most effective, drug testing concerns with full-spectrum, and how to choose for your purpose.", "category": "Education"},
    {"slug": "cannabis-and-sleep",            "title": "Cannabis, CBD and Sleep — What Does the Research Actually Say?",         "brief": "Evidence-based look at cannabis and sleep: what the research shows about CBD for sleep vs THC for sleep, how cannabinoids affect sleep architecture (REM, deep sleep), endocannabinoid involvement in circadian rhythm, studies on CBD for insomnia, cautions and limitations, and the difference between anecdotal reports and clinical evidence.", "category": "Education"},
    {"slug": "cannabis-and-anxiety",          "title": "CBD and Anxiety — What the Science Says in 2026",                       "brief": "Balanced, evidence-based look at CBD and anxiety: what anxiety disorders are, what the research shows (studies, doses, outcomes), how CBD may interact with serotonin receptors, difference between CBD and THC effects on anxiety, important caveats, limitations of current research, and Ghana context (mental health, stigma).", "category": "Education"},
    {"slug": "how-to-read-cannabis-lab-report", "title": "How to Read a Cannabis Lab Report — A Complete Guide",                 "brief": "Practical guide to understanding a Certificate of Analysis (CoA): what gets tested (cannabinoid profile, terpenes, pesticides, heavy metals, microbials, residual solvents), how to find the THC percentage, what full-spectrum vs isolate looks like on a report, red flags, and why Ghana's NACOC requires THC compliance testing.", "category": "Education"},
    {"slug": "hempcrete-explained",           "title": "Hempcrete — The Building Material That Could Transform Ghanaian Construction", "brief": "What is hempcrete: composition (hemp hurd + lime + water), properties (insulation, breathability, carbon negative, fire resistant, pest resistant), how to build with it, how it compares to concrete, cost comparison, projects worldwide, and the massive potential for sustainable construction in Ghana and across West Africa.", "category": "Education"},
    {"slug": "history-cannabis-africa",       "title": "The History of Cannabis in Africa — From Ancient Use to Modern Regulation", "brief": "Deep history of cannabis in Africa: earliest evidence of cannabis use on the continent, spread of cannabis from Central Asia through East Africa, traditional medical and spiritual uses across tribes and regions, colonial-era prohibition, post-independence drug laws, and the new wave of African countries building legal frameworks including Ghana.", "category": "Education"},
    {"slug": "hemp-vs-marijuana",             "title": "Hemp vs Marijuana — What Is Actually the Difference?",                  "brief": "Clear explanation of hemp vs marijuana: same species (Cannabis sativa), different cultivation purposes and THC content, legal difference (0.3% THC threshold), visual differences in the plant, what each is used for, why the distinction matters legally in Ghana, and common misconceptions.", "category": "Education"},
    {"slug": "cannabis-strains-explained",    "title": "Cannabis Strains Explained — Indica, Sativa, Hybrid and Chemovars",      "brief": "Modern guide to cannabis strains: the traditional indica/sativa/hybrid classification and why it is outdated, the move to chemovars (chemical variety), how THC/CBD ratios define effects more than species, terpene profiles, what this means for medicinal cannabis, and how Ghana's research licences are exploring cannabinoid profiles.", "category": "Education"},
    {"slug": "what-is-a-cannabis-tincture",   "title": "What Is a Cannabis Tincture? How to Use It and What to Expect",          "brief": "Complete guide to cannabis tinctures: what they are (alcohol-based cannabis extracts), how they differ from oil, how to use them (sublingual dosing), onset and duration, how to dose properly, how to make a simple hemp tincture, benefits vs other consumption methods, and legal considerations in Ghana.", "category": "Education"},
    {"slug": "industrial-hemp-uses-full",     "title": "40+ Uses of Industrial Hemp — The Most Useful Plant on Earth",            "brief": "Comprehensive list of industrial hemp applications across all sectors: fibre (textiles, rope, paper, bioplastics), seeds (food, oil, animal feed), flower (CBD, aromatherapy), hurd (hempcrete, animal bedding, biofuel), roots (traditional medicine), and emerging uses (graphene replacement, biodegradable packaging). Ghana-specific applications throughout.", "category": "Education"},
    {"slug": "how-to-store-hemp-cbd-products", "title": "How to Store Hemp and CBD Products — Keep Them Fresh and Potent",       "brief": "Practical guide to storing hemp and CBD products: how light, heat, air and moisture degrade cannabinoids, ideal storage conditions for CBD oil, hemp seeds, hemp flower, edibles and tinctures, shelf life of different products, signs of degradation, best containers, and why proper storage matters for potency.", "category": "Education"},
]

BLOG_TOPICS = [
    {"slug": "ghana-cannabis-opportunity-west-africa", "title": "Ghana Has a Once-in-a-Generation Opportunity to Lead West Africa's Cannabis Economy", "brief": "Original opinion piece: argue that Ghana's 2026 cannabis framework, combined with its political stability, existing agricultural infrastructure, and access to international markets, positions it to become the dominant cannabis economy in West Africa. Compare to Lesotho's early-mover success in Southern Africa. Include risks.", "category": "Opinion"},
    {"slug": "why-small-farmers-must-not-be-left-behind", "title": "Why Ghana's Cannabis Revolution Must Not Leave Small Farmers Behind", "brief": "Analysis piece on the Supreme Court fee challenge: argue that if Ghana's licensing fees price out small-scale farmers, the sector will be captured by corporations and the economic benefits will bypass rural communities. Reference the constitutional petition. Propose solutions: tiered fees, cooperative licensing, farmer support programmes.", "category": "Opinion"},
    {"slug": "cbd-snake-oil-or-science",      "title": "CBD — Miracle Cure, Snake Oil, or Something in Between?",               "brief": "Balanced analysis of the CBD industry: what the robust clinical evidence shows (epilepsy, anxiety, inflammation), where the evidence is weak or anecdotal, how marketing has outrun science, why consumers need to be sceptical, what quality standards exist, and what Ghana should regulate. Take a clear evidence-based position.", "category": "Analysis"},
    {"slug": "africa-cannabis-race-who-will-win", "title": "The African Cannabis Race — Which Country Will Win and Why",         "brief": "Comparative analysis of African cannabis markets: Morocco (established), Lesotho (first mover), South Africa (decriminalisation), Zimbabwe, Ghana (new entrant). Argue which country is best positioned to capture the global export market and why. Include factors: regulatory clarity, agricultural capacity, proximity to EU, political stability.", "category": "Analysis"},
    {"slug": "nacoc-intermediary-warning-what-it-means", "title": "NACOC's Intermediary Warning Is a Sign the Industry Is Already Being Exploited", "brief": "Deep analysis of NACOC's warning that no intermediaries are authorised: why this warning was necessary, what is likely happening on the ground (fraudsters taking money from farmers), what NACOC should do to protect applicants, and what applicants should watch out for. Include practical advice.", "category": "Analysis"},
    {"slug": "hemp-farming-ghana-real-economics", "title": "The Real Economics of Hemp Farming in Ghana — What the Numbers Say",  "brief": "Data-driven analysis of hemp farming economics in Ghana: estimated yields per hectare for fibre vs CBD hemp, price per kg of raw fibre vs CBD biomass on international markets, cost of getting a licence (fees, documents, compliance), estimated farm setup costs, realistic revenue projections, break-even timeline, and comparison to cocoa farming income.", "category": "Analysis"},
    {"slug": "czechrepublic-ghana-cannabis-partnership", "title": "Inside Ghana's Cannabis Partnership with the Czech Republic",    "brief": "Deep dive into the Czech Republic-Ghana cannabis collaboration: what has been reported, what the Czech Republic's own cannabis framework looks like, what expertise they bring, what Ghana gets in return, whether this is export-oriented, and what this means for Ghana's position in the European cannabis market.", "category": "Analysis"},
    {"slug": "cannabis-medicine-ghana-future", "title": "Could Cannabis Medicine Change Healthcare in Ghana?",                   "brief": "Exploration of medicinal cannabis potential in Ghana: what conditions affect Ghanaian patients where cannabis research shows promise (chronic pain, epilepsy, sickle cell, cancer side-effects, mental health), current state of Ghana's pharmaceutical sector, what a licensed R&D programme could produce, and what barriers exist (stigma, infrastructure, regulation).", "category": "Health"},
]

SEO_GUIDES = [
    {"slug": "how-to-apply-cannabis-licence-ghana-nacoc",          "keyword": "how to apply for cannabis licence Ghana",              "title": "How to Apply for a Cannabis Licence in Ghana — NACOC Step-by-Step Guide 2026",      "category": "Licensing", "brief": "Complete step-by-step guide to applying on portal.ncc.gov.gh. All 11 licence categories, eligibility, 12-document checklist, fees, timeline, what happens after you apply. Target: Ghanaian farmers, entrepreneurs, foreign investors."},
    {"slug": "nacoc-cannabis-licence-requirements-checklist",       "keyword": "NACOC cannabis licence requirements Ghana",            "title": "NACOC Cannabis Licence Requirements — Full Document Checklist 2026",               "category": "Licensing", "brief": "Every document needed per category. Citizenship rules, 50% ownership rule, environmental permits, site master file, SOPs, off-taker agreements. Practical checklist format."},
    {"slug": "how-to-start-hemp-farming-ghana",                     "keyword": "hemp farming Ghana how to start",                     "title": "How to Start Hemp Farming in Ghana — Complete Grower's Guide 2026",               "category": "Farming",  "brief": "Practical guide: 8 cultivation tiers (1 acre to 15,000+ ha), approved cultivar varieties, off-taker agreements, environmental permits, soil requirements, harvest, what happens post-harvest. Include realistic costs."},
    {"slug": "ghana-cannabis-investment-guide-2026",                "keyword": "Ghana cannabis investment opportunities",             "title": "Ghana Cannabis Investment Guide 2026 — Opportunities, Rules and How to Enter",     "category": "Business", "brief": "For investors: Cannacham $1B projection, 50% ownership rule, best licence categories for ROI, how to find Ghanaian partners, Czech Republic model, risks, timelines."},
    {"slug": "li-2475-ghana-cannabis-law-explained",                "keyword": "LI 2475 Ghana cannabis law explained",                "title": "L.I. 2475 Ghana Cannabis Law — Plain English Breakdown 2026",                   "category": "Policy",   "brief": "Plain English: what it allows, what it prohibits, how it differs from Act 1019 and Act 1100, THC 0.3% limit, NACOC authority, penalties, comparison to other African cannabis laws."},
    {"slug": "is-cannabis-legal-ghana-2026",                        "keyword": "is cannabis legal in Ghana",                         "title": "Is Cannabis Legal in Ghana? The Complete Answer for 2026",                       "category": "Policy",   "brief": "Recreational = illegal, medicinal/industrial with licence = legal. THC limit, penalties, Act 1100, L.I. 2475, comparison with South Africa, Lesotho, Nigeria."},
    {"slug": "nacoc-ghana-contact-portal-guide",                    "keyword": "NACOC Ghana portal how to apply",                    "title": "NACOC Ghana — Official Contact Details, Portal Guide and Application Steps",      "category": "Licensing","brief": "portal.ncc.gov.gh step by step, email, toll-free number, physical address, inside the portal, common mistakes, processing times, rejected applications."},
    {"slug": "industrial-hemp-uses-ghana",                          "keyword": "industrial hemp uses Ghana",                         "title": "Industrial Hemp Uses in Ghana — What Can Be Made Under L.I. 2475",              "category": "Education","brief": "All permitted uses: textiles, hempcrete, CBD, biofuels, paper, animal feed, food products, medicinal. Export potential per category."},
    {"slug": "africa-cannabis-regulation-comparison-2026",          "keyword": "Africa cannabis regulation country comparison",      "title": "Africa Cannabis Regulation 2026 — Country-by-Country Guide",                     "category": "Africa",   "brief": "Ghana, South Africa, Lesotho, Zimbabwe, Morocco, Rwanda, Nigeria, Malawi, Zambia. Table format. Who's ahead and why."},
    {"slug": "ghana-hemp-export-guide",                             "keyword": "how to export hemp from Ghana",                      "title": "How to Export Hemp from Ghana — NACOC Export Licence Complete Guide",            "category": "Business", "brief": "Export licence requirements, destruction plan, which products can be exported, destination countries, EU market requirements, finding international buyers, Czech Republic opportunity."},
    {"slug": "ghana-medicinal-cannabis-programme-guide",            "keyword": "Ghana medicinal cannabis programme",                 "title": "Ghana Medicinal Cannabis Programme — Who Qualifies and How to Apply",            "category": "Education","brief": "Conditions being researched (pain, epilepsy, neuropathy, chemo side effects), CED Clinical research, R&D licence, pathway from research to approved medicine."},
    {"slug": "cbd-oil-ghana-legal-buy",                             "keyword": "CBD oil Ghana legal buy",                           "title": "Is CBD Oil Legal in Ghana? Where to Buy and What to Know",                      "category": "Policy",   "brief": "Legal status of CBD oil under L.I. 2475, what's available, what's not, how to source legally, what NACOC licences cover CBD products, consumer guidance."},
    {"slug": "hemp-seed-oil-ghana-benefits",                        "keyword": "hemp seed oil Ghana benefits",                      "title": "Hemp Seed Oil Ghana — Benefits, Uses and Where to Find It",                     "category": "Education","brief": "Nutritional profile, omega-3/6 ratio, skin benefits, cooking uses, difference from CBD oil, whether it contains THC, where to find in Ghana, licensed producers."},
    {"slug": "cannabis-ghana-news-2026",                            "keyword": "Ghana cannabis news 2026",                          "title": "Ghana Cannabis News 2026 — Everything That Has Happened",                        "category": "Ghana News","brief": "Chronological: February 26 minister launch, Supreme Court petition, NACOC intermediary warning, Czech Republic talks, Cannacham $1B projection, CED Clinical research. Updated regularly."},
]

TRENDING_SEARCH_TOPICS = [
    "cannabis CBD benefits 2026", "hemp uses daily life", "CBD oil side effects",
    "hemp protein benefits", "cannabis mental health", "hemp building materials",
    "CBD dosage guide", "cannabis Africa legalization", "hemp farming profit",
    "terpenes cannabis guide", "CBG vs CBD", "hemp food products",
    "cannabis investment Africa", "CBD sleep aid", "hemp skincare benefits",
    "cannabis anxiety research", "hemp vs cotton environment", "CBD isolate vs full spectrum",
    "cannabis pain relief", "hemp bioplastics future",
]

# ═══════════════════════════════════════════════════════
# SHARED HTML TEMPLATE
# ═══════════════════════════════════════════════════════

def build_html_page(title, meta_desc, keywords, filename, category, date_str, iso_date,
                    read_time, body_html, sources_html, article_type="Article",
                    toc_html="", show_legal=True):
    schema_type = "NewsArticle" if article_type == "NewsArticle" else "Article"
    legal_box = ""
    if show_legal:
        legal_box = """<div class="legal-box">
      <div class="lt">Legal Reminder</div>
      <p>Recreational cannabis remains strictly illegal in Ghana. This content covers the legal industrial hemp and medicinal cannabis sector governed by Act 1100 (2023) and L.I. 2475 (2023). All licensed activities require a valid NACOC licence. Apply at <a href="https://portal.ncc.gov.gh/#licences" style="color:#CE1126;">portal.ncc.gov.gh</a>. Not legal advice.</p>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — GhanaHemp.com</title>
<meta name="description" content="{meta_desc}">
<meta name="keywords" content="{keywords}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<link rel="canonical" href="https://ghanahemp.com/{filename}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"{schema_type}","headline":"{title}","description":"{meta_desc}","publisher":{{"@type":"Organization","name":"GhanaHemp.com","url":"https://ghanahemp.com"}},"datePublished":"{iso_date}","dateModified":"{iso_date}","mainEntityOfPage":{{"@type":"WebPage","@id":"https://ghanahemp.com/{filename}"}}}}
</script>
<style>
:root{{--red:#CE1126;--gold:#FCD116;--green:#006B3F;--black:#0D0D0D;--cream:#FAF8F3;--warm:#F2EDE3;--border:#E2DDD3;--text:#1C1A17;--muted:#6B6660;}}
*{{margin:0;padding:0;box-sizing:border-box;}}body{{font-family:'IBM Plex Sans',sans-serif;background:var(--cream);color:var(--text);}}
.wrap{{max-width:800px;margin:0 auto;padding:0 32px;}}
.flag{{display:flex;height:5px;}}.fr{{flex:1;background:#CE1126;}}.fg{{flex:1;background:#FCD116;}}.fgr{{flex:1;background:#006B3F;}}
.topbar{{background:#0D0D0D;color:rgba(255,255,255,.45);font-family:'IBM Plex Mono',monospace;font-size:10px;padding:7px 32px;display:flex;justify-content:space-between;}}
.topbar a{{color:rgba(255,255,255,.4);text-decoration:none;margin-left:16px;}}
.masthead{{background:var(--cream);border-bottom:2px solid #0D0D0D;padding:18px 32px;}}
.sn{{font-family:'Libre Baskerville',serif;font-size:32px;font-weight:700;letter-spacing:-1px;color:#0D0D0D;text-decoration:none;}}.sn span{{color:#006B3F;}}
nav{{background:#0D0D0D;display:flex;padding:0 32px;overflow-x:auto;}}
nav a{{color:rgba(255,255,255,.68);text-decoration:none;font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.11em;text-transform:uppercase;padding:13px;border-bottom:3px solid transparent;white-space:nowrap;}}
nav a:hover{{color:#FCD116;border-bottom-color:#FCD116;}}
nav a.cta{{background:#006B3F;color:#fff;margin-left:auto;border-bottom:none!important;}}
.hero{{background:#0D0D0D;padding:52px 32px;position:relative;overflow:hidden;}}
.hero::before{{content:'';position:absolute;inset:0;opacity:.04;background-image:repeating-linear-gradient(0deg,#FCD116 0,#FCD116 1px,transparent 1px,transparent 44px),repeating-linear-gradient(90deg,#FCD116 0,#FCD116 1px,transparent 1px,transparent 44px);}}
.eyebrow{{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.22em;text-transform:uppercase;color:#FCD116;margin-bottom:14px;display:flex;align-items:center;gap:10px;position:relative;z-index:1;}}
.eyebrow::before{{content:'';width:24px;height:2px;background:#FCD116;}}
.hero h1{{font-family:'Libre Baskerville',serif;font-size:40px;font-weight:700;color:#fff;line-height:1.12;letter-spacing:-.6px;margin-bottom:16px;position:relative;z-index:1;}}
.byline{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:rgba(255,255,255,.4);position:relative;z-index:1;}}
.toc{{background:#fff;border:1px solid var(--border);padding:24px 28px;margin:36px 0;}}
.toc-title{{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin-bottom:14px;}}
.toc ol{{padding-left:20px;}}.toc li{{font-size:14px;line-height:1.9;}}
.toc a{{color:#006B3F;text-decoration:none;}}
.body{{padding:48px 0 80px;}}
.body p{{font-size:16px;line-height:1.85;color:var(--text);margin-bottom:24px;}}
.body h2{{font-family:'Libre Baskerville',serif;font-size:26px;font-weight:700;margin:48px 0 18px;line-height:1.2;padding-top:8px;border-top:2px solid var(--border);}}
.body h3{{font-family:'Libre Baskerville',serif;font-size:20px;font-weight:700;margin:32px 0 12px;color:#006B3F;}}
.body ul,.body ol{{padding-left:24px;margin-bottom:24px;}}
.body li{{font-size:15px;line-height:1.85;margin-bottom:6px;}}
.body blockquote{{border-left:3px solid #FCD116;padding:16px 20px;margin:28px 0;background:#fff;}}
.body blockquote p{{font-style:italic;font-size:15px;margin-bottom:4px;}}
.body blockquote cite{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--muted);font-style:normal;}}
.callout{{background:var(--warm);border-left:4px solid #006B3F;padding:20px 24px;margin:28px 0;}}
.callout p{{margin-bottom:0;font-size:15px;}}
.fact-box{{background:#fff;border:1px solid var(--border);padding:20px 24px;margin:28px 0;}}
.fact-box .fb-label{{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:#006B3F;margin-bottom:12px;font-weight:600;}}
.legal-box{{background:#fff8f8;border-left:4px solid #CE1126;padding:18px 20px;margin:32px 0;}}
.legal-box .lt{{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.17em;text-transform:uppercase;color:#CE1126;margin-bottom:6px;font-weight:600;}}
.legal-box p{{font-size:13px;color:var(--muted);line-height:1.62;margin-bottom:0;}}
.source-box{{background:var(--warm);border:1px solid var(--border);padding:16px 20px;margin:32px 0;font-family:'IBM Plex Mono',monospace;font-size:9px;color:var(--muted);line-height:1.8;}}
.source-box a{{color:#006B3F;text-decoration:none;}}
.faq{{margin:40px 0;}}.faq-item{{border-bottom:1px solid var(--border);padding:18px 0;}}
.faq-q{{font-family:'Libre Baskerville',serif;font-size:17px;font-weight:700;margin-bottom:10px;}}
.faq-a{{font-size:15px;line-height:1.75;}}
.related{{border-top:2px solid #0D0D0D;padding-top:32px;margin-top:48px;}}
.related h4{{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;margin-bottom:16px;}}
.related a{{display:block;font-family:'Libre Baskerville',serif;font-size:16px;font-weight:700;color:var(--text);text-decoration:none;padding:12px 0;border-bottom:1px solid var(--border);transition:color .2s;}}
.related a:hover{{color:#006B3F;}}
footer{{background:#0D0D0D;color:rgba(255,255,255,.4);padding:32px;font-family:'IBM Plex Mono',monospace;font-size:9px;text-align:center;line-height:1.8;}}
footer a{{color:rgba(255,255,255,.3);text-decoration:none;margin:0 8px;}}
@media(max-width:600px){{.hero h1{{font-size:28px;}}.wrap{{padding:0 20px;}}}}
</style>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9XY6MSVR1K"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-9XY6MSVR1K');
</script>
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4797924476772764"
     crossorigin="anonymous"></script>
</head>
<body>
<div class="flag"><div class="fr"></div><div class="fg"></div><div class="fgr"></div></div>
<div class="topbar"><span>NACOC Licensing Portal Open — portal.ncc.gov.gh · Toll-Free: 0800 307 307</span><div><a href="index.html">Home</a><a href="ghana-news.html">Ghana News</a><a href="licensing.html">Licensing</a></div></div>
<div class="masthead"><a href="index.html" class="sn">Ghana<span>Hemp</span>.com</a></div>
<nav><a href="index.html">Home</a><a href="ghana-news.html">Ghana News</a><a href="licensing.html">Licensing</a><a href="business.html">Business</a><a href="policy.html">Policy</a><a href="africa.html">Africa</a><a href="world.html">World</a><a href="education.html">Education</a><a href="resources.html">Resources</a><a href="index.html#newsletter" class="cta">Newsletter</a></nav>
<div class="hero"><div class="wrap"><div class="eyebrow">{category} — {date_str}</div><h1>{title}</h1><div class="byline">GhanaHemp.com — {date_str} — {read_time} min read</div></div></div>
<div class="body"><div class="wrap">
{toc_html}
{body_html}
<div class="source-box"><strong>Sources &amp; References:</strong><br>{sources_html}</div>
{legal_box}
<div class="related"><h4>Related Reading</h4><a href="licensing.html">NACOC Licensing Guide — All 11 Categories</a><a href="policy.html">Ghana Cannabis Law — Full Legal Analysis</a><a href="ghana-news.html">Latest Ghana Cannabis News</a><a href="education.html">Education Hub</a><a href="business.html">Business &amp; Investment</a></div>
</div></div>
<footer>© 2026 GhanaHemp.com — Ghana's Independent Hemp &amp; Cannabis News Authority<br>Not legal or medical advice. Info sourced from ncc.gov.gh · mint.gov.gh<br><br><a href="index.html">Home</a><a href="ghana-news.html">News</a><a href="licensing.html">Licensing</a><a href="education.html">Education</a><a href="resources.html">Resources</a></footer>
</body></html>"""


def build_toc(sections):
    if not sections:
        return ""
    items = "".join(f'<li><a href="#s{i}">{s}</a></li>\n' for i, s in enumerate(sections, 1))
    return f'<div class="toc"><div class="toc-title">In This Article</div><ol>\n{items}</ol></div>'


# ═══════════════════════════════════════════════════════
# GITHUB HELPERS
# ═══════════════════════════════════════════════════════

def get_existing_files():
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/", headers=headers)
    return [f['name'] for f in r.json()] if r.status_code == 200 else []


def publish_to_github(filename, html_content, commit_msg=None):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    content_b64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    check = requests.get(url, headers=headers)
    payload = {
        "message": commit_msg or f"{'Update' if check.status_code == 200 else 'New'}: {filename} [{date_str}]",
        "content": content_b64, "branch": "main"
    }
    if check.status_code == 200:
        payload["sha"] = check.json()["sha"]
    r = requests.put(url, headers=headers, json=payload)
    if r.status_code in (200, 201):
        print(f"  ✅ https://ghanahemp.com/{filename}")
        return True
    print(f"  ❌ GitHub error {r.status_code}: {r.text[:150]}")
    return False


def update_news_index(filename, headline, summary, category):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/ghana-news.html"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return False
    data = r.json()
    current = base64.b64decode(data['content']).decode('utf-8')
    sha = data['sha']
    date_str = datetime.datetime.now().strftime('%B %d, %Y')
    snip = (summary[:135] + '...') if len(summary) > 135 else summary
    card = f"""
  <div class="card" style="border:2px solid var(--green);">
    <div class="ct"><div class="cti tg"></div><div class="clbl lg">{category} — NEW</div></div>
    <h3><a href="{filename}" style="text-decoration:none;color:inherit;">{headline}</a></h3>
    <p>{snip}</p>
    <div class="src">GhanaHemp.com — {date_str} — <a href="{filename}">Read full article</a></div>
  </div>
"""
    marker = '<div class="grid g2">'
    if marker not in current:
        return False
    updated = current.replace(marker, marker + card, 1)
    updated_b64 = base64.b64encode(updated.encode('utf-8')).decode('utf-8')
    r2 = requests.put(url, headers=headers, json={"message": f"Index updated: {date_str}", "content": updated_b64, "sha": sha, "branch": "main"})
    return r2.status_code in (200, 201)


def slugify(text, max_len=55):
    s = text.lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'\s+', '-', s.strip())
    return s[:max_len]


def today():
    return datetime.datetime.now().strftime('%B %d, %Y')

def today_iso():
    return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

def read_time(html):
    return max(3, round(len(html.split()) / 200))


# ═══════════════════════════════════════════════════════
# AI HELPERS — call Claude with web search
# ═══════════════════════════════════════════════════════

def ai_search_and_write(prompt, max_tokens=4000, use_search=True):
    """Call Claude Sonnet with optional web search. Returns full text."""
    tools = [{"type": "web_search_20250305", "name": "web_search"}] if use_search else []
    kwargs = dict(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    if tools:
        kwargs["tools"] = tools
    r = client.messages.create(**kwargs)
    return "".join(b.text for b in r.content if hasattr(b, 'text'))


def ai_write(prompt, max_tokens=3000):
    """Call Claude Haiku — fast writer, no search."""
    r = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text.strip()


def parse_sections(text):
    """Extract SECTIONS_JSON from AI output."""
    if "SECTIONS_JSON:" in text:
        parts = text.split("SECTIONS_JSON:")
        try:
            return parts[0].strip(), json.loads(parts[1].strip())
        except:
            return parts[0].strip(), []
    return text.strip(), []


# ═══════════════════════════════════════════════════════
# TWITTER / X AUTO-POSTING
# ═══════════════════════════════════════════════════════

HASHTAG_SETS = {
    "news":        "#GhanaHemp #NACOC #GhanaCannabis #Hemp #Ghana",
    "educational": "#Hemp #CBD #GhanaHemp #HempEducation #Cannabis",
    "blog":        "#GhanaHemp #CannabisAfrica #HempGhana #Ghana",
    "research":    "#Hemp #Cannabis #GhanaHemp #AfricaCannabis",
    "seo":         "#GhanaHemp #NACOC #GhanaCannabis #HempGhana",
}

TWEET_TEMPLATES = {
    "news": [
        "🇬🇭 BREAKING: {headline}\n\n{summary}\n\n{url}\n\n{tags}",
        "🌿 Ghana Cannabis Update:\n\n{headline}\n\n{summary}\n\n{url}\n\n{tags}",
        "📰 Latest from Ghana's hemp sector:\n\n{headline}\n\n{url}\n\n{tags}",
    ],
    "educational": [
        "📚 Did you know? {headline}\n\n{summary}\n\nFull guide 👇\n{url}\n\n{tags}",
        "🌿 Hemp & CBD education:\n\n{headline}\n\n{summary}\n\n{url}\n\n{tags}",
        "Learn something new today 👇\n\n{headline}\n\n{url}\n\n{tags}",
    ],
    "blog": [
        "💡 New analysis on GhanaHemp.com:\n\n{headline}\n\n{summary}\n\n{url}\n\n{tags}",
        "🔍 Opinion: {headline}\n\n{summary}\n\nRead the full piece 👇\n{url}\n\n{tags}",
        "We need to talk about this 👇\n\n{headline}\n\n{url}\n\n{tags}",
    ],
    "research": [
        "🔬 New research article:\n\n{headline}\n\n{summary}\n\n{url}\n\n{tags}",
        "🌍 {headline}\n\n{summary}\n\nFull article 👇\n{url}\n\n{tags}",
    ],
    "seo": [
        "📋 Complete guide: {headline}\n\n{summary}\n\n{url}\n\n{tags}",
        "Everything you need to know 👇\n\n{headline}\n\n{url}\n\n{tags}",
        "🇬🇭 {headline}\n\n{summary}\n\n{url}\n\n{tags}",
    ],
}


def get_twitter_client():
    """Return authenticated tweepy client or None if credentials missing."""
    if not TWEEPY_AVAILABLE:
        return None
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        print("  ⚠️  Twitter credentials not set — skipping Twitter post")
        return None
    try:
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        return client
    except Exception as e:
        print(f"  ⚠️  Twitter auth failed: {e}")
        return None


def build_tweet(mode, headline, summary, filename):
    """Build a tweet under 280 characters."""
    url = f"https://ghanahemp.com/{filename}"
    tags = HASHTAG_SETS.get(mode, HASHTAG_SETS["news"])
    templates = TWEET_TEMPLATES.get(mode, TWEET_TEMPLATES["news"])
    template = random.choice(templates)

    # Truncate summary to fit
    summary_short = (summary[:100] + "...") if len(summary) > 100 else summary

    tweet = template.format(
        headline=headline,
        summary=summary_short,
        url=url,
        tags=tags
    )

    # Hard trim to 280 chars — preserve URL and tags at end
    if len(tweet) <= 280:
        return tweet

    # If too long, use minimal template
    minimal = f"🌿 {headline}\n\n{url}\n\n{tags}"
    if len(minimal) <= 280:
        return minimal

    # Last resort — just headline + url + one hashtag
    return f"🌿 {headline[:180]}...\n\n{url}\n\n#GhanaHemp"[:280]


def post_to_twitter(mode, headline, summary, filename):
    """Post a tweet. Returns True on success."""
    print("  🐦 Posting to Twitter/X (@hempghana)...")
    client = get_twitter_client()
    if not client:
        return False

    tweet_text = build_tweet(mode, headline, summary, filename)

    try:
        response = client.create_tweet(text=tweet_text)
        if response.data:
            tweet_id = response.data.get("id", "")
            print(f"  ✅ Tweet posted: https://twitter.com/hempghana/status/{tweet_id}")
            return True
        else:
            print("  ❌ Tweet failed — no response data")
            return False
    except tweepy.TweepyException as e:
        print(f"  ❌ Tweet failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Tweet error: {e}")
        return False


# ═══════════════════════════════════════════════════════
# MODE 1 — BREAKING NEWS
# ═══════════════════════════════════════════════════════

def run_news_mode():
    print("\n📡 MODE 1: NEWS")
    raw = ai_search_and_write("""Search for the LATEST Ghana cannabis, hemp, or NACOC news from the past 7 days.

Search: "Ghana cannabis 2026" AND "NACOC cannabis Ghana" AND check: modernghana.com, myjoyonline.com, citinewsroom.com, 3news.com, graphic.com.gh, theafricareport.com

Find the single most important, most recent story published in the last 7 days.

Return ONLY this JSON (no other text):
{
  "has_news": true,
  "headline": "exact headline",
  "summary": "2-3 sentence factual summary",
  "source_url": "URL",
  "source_name": "publication name",
  "category": "Policy or Licensing or Business or Legal or Health or Industry",
  "date": "date"
}""", max_tokens=1000)

    try:
        m = re.search(r'\{.*?\}', raw, re.DOTALL)
        news = json.loads(m.group()) if m else {}
    except:
        news = {}

    if not news.get('has_news'):
        print("  No news found today.")
        return False

    headline = news.get('headline', '')
    category = news.get('category', 'Ghana News')
    print(f"  Found: {headline}")

    time.sleep(20)

    body = ai_write(f"""You are GhanaHemp.com's lead journalist. Write a 700-word news article in HTML.

HEADLINE: {headline}
SUMMARY: {news.get('summary')}
SOURCE: {news.get('source_name')}
CATEGORY: {category}

WRITING RULES:
- Write in GhanaHemp.com's authoritative voice — factual, serious, Ghana-first
- DO NOT just restate the summary. Expand on it with context, background, analysis
- Use ONLY these HTML tags: <p>, <h2>, <h3>, <blockquote><p></p><cite></cite></blockquote>
- 4 sections with descriptive h2 headings
- Include context: reference NACOC, L.I. 2475, Act 1100, portal.ncc.gov.gh where relevant
- End with a "What This Means" section analysing the implications for Ghana
- Reference the source but write the article in our own original voice
- Return ONLY the HTML body, nothing else""", max_tokens=2500)

    filename = f"article-{datetime.datetime.now().strftime('%Y-%m-%d')}-{slugify(headline)}.html"
    sources_html = f'<a href="{news.get("source_url","")}" target="_blank">{news.get("source_name","")}</a> · NACOC (ncc.gov.gh) · Ministry of Interior (mint.gov.gh)'

    html = build_html_page(
        title=headline, meta_desc=news.get('summary','')[:155],
        keywords=f"Ghana cannabis news, NACOC, hemp Ghana, {category.lower()} Ghana",
        filename=filename, category=category, date_str=today(), iso_date=today_iso(),
        read_time=read_time(body), body_html=body, sources_html=sources_html,
        article_type="NewsArticle"
    )

    if publish_to_github(filename, html):
        time.sleep(2)
        update_news_index(filename, headline, news.get('summary',''), category)
        print(f"  Published news: {filename}")
        time.sleep(5)
        post_to_twitter("news", headline, news.get('summary',''), filename)
        return True
    return False


# ═══════════════════════════════════════════════════════
# MODE 2 — RESEARCH-DRIVEN ORIGINAL ARTICLE
# ═══════════════════════════════════════════════════════

def run_research_mode(existing_files):
    print("\n🔬 MODE 2: RESEARCH → ORIGINAL ARTICLE")

    # Step 1: Find what's trending + pick a research topic
    trend_query = random.choice(TRENDING_SEARCH_TOPICS)
    print(f"  Research topic: {trend_query}")

    raw = ai_search_and_write(f"""Research this topic thoroughly for a Ghana-focused cannabis/hemp website:

TOPIC: "{trend_query}"

Do the following:
1. Search Google Trends or news for what people are currently searching about this topic
2. Find 3-5 credible sources (research papers, news outlets, government sites, industry reports)
3. Identify the most interesting, current angle that would resonate with Ghanaian readers interested in cannabis/hemp

Then return ONLY this JSON:
{{
  "angle": "The specific angle/headline you will write about",
  "slug": "url-slug-like-this",
  "category": "Education or Business or Health or Science or Policy or Africa",
  "key_facts": ["fact 1", "fact 2", "fact 3", "fact 4", "fact 5"],
  "sources": ["source name 1 | URL 1", "source name 2 | URL 2", "source name 3 | URL 3"],
  "ghana_relevance": "How this topic directly relates to Ghana or Ghanaian readers"
}}""", max_tokens=1500)

    try:
        m = re.search(r'\{.*?\}', raw, re.DOTALL)
        plan = json.loads(m.group()) if m else {}
    except:
        plan = {}

    if not plan.get('angle'):
        print("  Could not build research plan, skipping.")
        return False

    angle = plan['angle']
    slug = plan.get('slug', slugify(angle))
    category = plan.get('category', 'Education')
    filename = f"research-{datetime.datetime.now().strftime('%Y-%m-%d')}-{slug}.html"

    if filename in existing_files:
        print(f"  Already published: {filename}, skipping.")
        return False

    print(f"  Writing: {angle}")
    time.sleep(15)

    raw2 = ai_write(f"""You are GhanaHemp.com's senior writer. Write a 900-word ORIGINAL article in HTML.

ANGLE: {angle}
CATEGORY: {category}
KEY FACTS: {json.dumps(plan.get('key_facts', []))}
GHANA RELEVANCE: {plan.get('ghana_relevance', '')}

THIS IS ORIGINAL JOURNALISM — NOT A SUMMARY:
- Write entirely in GhanaHemp.com's voice. This is not a rewrite of sources.
- Synthesise the facts into original analysis with a clear perspective
- Make it genuinely interesting and informative for Ghanaian readers
- Use ONLY these HTML tags: <p>, <h2>, <h3>, <ul><li>, <ol><li>, <blockquote><p></p><cite></cite></blockquote>, <div class="callout"><p></p></div>
- 4-5 sections with descriptive h2 headings, each with an id like id="s1" id="s2" etc.
- Add a Ghana context section connecting global trends to Ghana's cannabis opportunity
- End with a clear takeaway
- Return HTML body FIRST, then on a new line write:
SECTIONS_JSON:
["Section 1 Title", "Section 2 Title", "Section 3 Title", "Section 4 Title"]""", max_tokens=3500)

    body, sections = parse_sections(raw2)
    toc = build_toc(sections)
    sources_list = plan.get('sources', [])
    sources_html = ' · '.join(f'<a href="#" target="_blank">{s.split("|")[0].strip()}</a>' for s in sources_list)
    if not sources_html:
        sources_html = 'GhanaHemp.com Research · NACOC (ncc.gov.gh) · Cannabis research literature'

    html = build_html_page(
        title=angle, meta_desc=f"{angle}. Original analysis from GhanaHemp.com — Ghana's hemp and cannabis news authority.",
        keywords=f"{trend_query}, Ghana cannabis, hemp Ghana, {category.lower()}",
        filename=filename, category=category, date_str=today(), iso_date=today_iso(),
        read_time=read_time(body), body_html=body, sources_html=sources_html,
        toc_html=toc
    )

    if publish_to_github(filename, html):
        print(f"  Published research article: {filename}")
        time.sleep(5)
        post_to_twitter("research", angle, plan.get('ghana_relevance', angle)[:120], filename)
        return True
    return False


# ═══════════════════════════════════════════════════════
# MODE 3 — EDUCATIONAL CONTENT
# ═══════════════════════════════════════════════════════

def run_educational_mode(existing_files):
    print("\n📚 MODE 3: EDUCATIONAL")

    # Find next unwritten educational topic
    topic = None
    for t in EDUCATIONAL_TOPICS:
        fname = f"learn-{t['slug']}.html"
        if fname not in existing_files:
            topic = t
            filename = fname
            break

    if not topic:
        # All written — pick a random new one based on a trending term
        topic = random.choice(EDUCATIONAL_TOPICS)
        filename = f"learn-{topic['slug']}-{datetime.datetime.now().strftime('%Y%m%d')}.html"

    print(f"  Topic: {topic['title']}")

    raw = ai_write(f"""You are GhanaHemp.com's education editor. Write a comprehensive 900-1100 word educational article in HTML.

TITLE: {topic['title']}
BRIEF: {topic['brief']}
CATEGORY: {topic['category']}

WRITING RULES:
- Write for a general audience — assume zero prior knowledge
- Be accurate, clear and engaging. No jargon without explanation.
- Add Ghana context wherever possible (Ghana's regulations, Ghana's market, relevance to Ghanaian readers)
- Use ONLY these HTML tags:
    <p> paragraphs
    <h2 id="s1"> main sections (use id="s1", id="s2" etc.)
    <h3> subsections
    <ul><li> or <ol><li> lists
    <blockquote><p></p><cite></cite></blockquote> for scientific citations
    <div class="callout"><p></p></div> for key takeaway boxes
    <div class="fact-box"><div class="fb-label">Key Facts</div>...</div> for fact boxes
    <div class="faq"><div class="faq-item"><div class="faq-q">Q?</div><div class="faq-a">A.</div></div></div>
- Include a FAQ section at the end with 4-5 questions
- Minimum 900 words

Return HTML body FIRST then:
SECTIONS_JSON:
["Section 1", "Section 2", "Section 3", "Section 4", "Section 5"]""", max_tokens=4000)

    body, sections = parse_sections(raw)
    toc = build_toc(sections)
    sources_html = 'GhanaHemp.com Editorial · NACOC (ncc.gov.gh) · PubMed cannabis research · WHO cannabidiol report · Project CBD'

    html = build_html_page(
        title=topic['title'],
        meta_desc=f"{topic['title']}. Complete guide from GhanaHemp.com — Ghana's hemp and cannabis education hub.",
        keywords=f"{topic['slug'].replace('-',' ')}, hemp education Ghana, cannabis guide, CBD explained",
        filename=filename, category=topic['category'], date_str=today(), iso_date=today_iso(),
        read_time=read_time(body), body_html=body, sources_html=sources_html,
        toc_html=toc
    )

    if publish_to_github(filename, html):
        print(f"  Published educational: {filename}")
        time.sleep(5)
        post_to_twitter("educational", topic['title'], topic['brief'][:120], filename)
        return True
    return False


# ═══════════════════════════════════════════════════════
# MODE 4 — ORIGINAL BLOG / OPINION / ANALYSIS
# ═══════════════════════════════════════════════════════

def run_blog_mode(existing_files):
    print("\n✍️  MODE 4: ORIGINAL BLOG")

    # Find next unwritten blog
    topic = None
    for t in BLOG_TOPICS:
        fname = f"blog-{t['slug']}.html"
        if fname not in existing_files:
            topic = t
            filename = fname
            break

    if not topic:
        topic = BLOG_TOPICS[0]
        filename = f"blog-{topic['slug']}-{datetime.datetime.now().strftime('%Y%m%d')}.html"

    print(f"  Topic: {topic['title']}")

    raw = ai_search_and_write(f"""You are GhanaHemp.com's senior analyst. Write a 900-word original opinion/analysis article.

TITLE: {topic['title']}
BRIEF: {topic['brief']}
CATEGORY: {topic['category']}

THIS IS ORIGINAL OPINION/ANALYSIS — not a news report:
- Take a clear position. Argue a point. Don't sit on the fence.
- Use evidence and reasoning to support your arguments
- Be bold, intelligent, and thought-provoking
- GhanaHemp.com's voice: authoritative, passionate about Ghana's hemp future, evidence-based
- Include real data, real numbers, real examples wherever possible
- Use web search to find supporting facts and data
- Use ONLY these HTML tags:
    <p>, <h2 id="s1">, <h3>, <ul><li>, <blockquote><p></p><cite></cite></blockquote>
    <div class="callout"><p></p></div>
- 4-5 sections
- End with a clear call to action or challenge to the reader

Return HTML body FIRST then:
SECTIONS_JSON:
["Section 1", "Section 2", "Section 3", "Section 4"]""", max_tokens=3500)

    body, sections = parse_sections(raw)
    toc = build_toc(sections)
    sources_html = 'GhanaHemp.com Analysis · NACOC (ncc.gov.gh) · cannacham.org · Industry research'

    html = build_html_page(
        title=topic['title'],
        meta_desc=f"{topic['title']}. Original analysis by GhanaHemp.com.",
        keywords=f"Ghana cannabis analysis, hemp Ghana opinion, cannabis Africa, {topic['slug'].replace('-',' ')}",
        filename=filename, category=topic['category'], date_str=today(), iso_date=today_iso(),
        read_time=read_time(body), body_html=body, sources_html=sources_html,
        toc_html=toc
    )

    if publish_to_github(filename, html):
        update_news_index(filename, topic['title'], topic['brief'][:150], topic['category'])
        print(f"  Published blog: {filename}")
        time.sleep(5)
        post_to_twitter("blog", topic['title'], topic['brief'][:120], filename)
        return True
    return False


# ═══════════════════════════════════════════════════════
# MODE 5 — SEO EVERGREEN GUIDE
# ═══════════════════════════════════════════════════════

def run_seo_mode(existing_files):
    print("\n🎯 MODE 5: SEO GUIDE")

    # Find next unwritten SEO guide
    target = None
    for t in SEO_GUIDES:
        fname = f"guide-{t['slug']}.html"
        if fname not in existing_files:
            target = t
            filename = fname
            break

    if not target:
        target = SEO_GUIDES[0]
        filename = f"guide-{target['slug']}-{datetime.datetime.now().strftime('%Y%m%d')}.html"

    print(f"  Keyword: {target['keyword']}")

    raw = ai_search_and_write(f"""You are GhanaHemp.com's SEO editor. Write a comprehensive 1100-word SEO guide in HTML.

TARGET KEYWORD: "{target['keyword']}"
TITLE: {target['title']}
BRIEF: {target['brief']}
CATEGORY: {target['category']}

SEO RULES — CRITICAL:
1. Use the exact keyword phrase naturally in the FIRST paragraph
2. Use related keywords throughout: Ghana cannabis, NACOC, hemp licence, L.I. 2475, Act 1100
3. Write for someone searching this exact query — answer their question completely
4. Include a FAQ section with 5 questions targeting related keywords
5. Use specific facts, numbers, dates — never vague generalisations
6. Minimum 1000 words

HTML TAGS — use ONLY:
- <p> paragraphs
- <h2 id="s1"> main sections (id="s1" etc)
- <h3> subsections
- <ul><li> or <ol><li> lists
- <div class="callout"><p></p></div> key callout boxes
- <div class="faq"><div class="faq-item"><div class="faq-q">Q?</div><div class="faq-a">A.</div></div></div>

Return HTML body FIRST then:
SECTIONS_JSON:
["Section 1", "Section 2", "Section 3", "Section 4", "FAQ"]""", max_tokens=4500)

    body, sections = parse_sections(raw)
    toc = build_toc(sections)
    keywords = f"{target['keyword']}, Ghana cannabis, NACOC licence, hemp Ghana, L.I. 2475, Act 1100, portal.ncc.gov.gh"
    sources_html = 'NACOC (ncc.gov.gh) · Ministry of Interior (mint.gov.gh) · cannacham.org · Act 1100 (2023) · L.I. 2475 (2023)'

    html = build_html_page(
        title=target['title'],
        meta_desc=target['brief'][:155],
        keywords=keywords, filename=filename, category=target['category'],
        date_str=today(), iso_date=today_iso(),
        read_time=read_time(body), body_html=body, sources_html=sources_html,
        toc_html=toc
    )

    if publish_to_github(filename, html):
        print(f"  Published SEO guide: {filename}")
        time.sleep(5)
        post_to_twitter("seo", target['title'], target['brief'][:120], filename)
        return True
    return False


# ═══════════════════════════════════════════════════════
# TRENDING TOPIC DETECTOR
# ═══════════════════════════════════════════════════════

def get_trending_topic():
    """Ask Claude what cannabis topics are trending today."""
    print("\n📈 Checking trending topics...")
    raw = ai_search_and_write("""Search Google Trends and recent news for what cannabis, hemp, and CBD topics people are searching for RIGHT NOW in 2026.

Search for:
1. Trending cannabis/hemp news globally this week
2. Trending CBD searches this week
3. What hemp/cannabis questions are people asking on Reddit and forums

Return ONLY a JSON array of 5 trending topic strings, like:
["topic 1", "topic 2", "topic 3", "topic 4", "topic 5"]

Return ONLY the JSON array, nothing else.""", max_tokens=800)

    try:
        m = re.search(r'\[.*?\]', raw, re.DOTALL)
        if m:
            topics = json.loads(m.group())
            print(f"  Trending: {topics[:3]}")
            return topics
    except:
        pass
    return TRENDING_SEARCH_TOPICS[:5]


# ═══════════════════════════════════════════════════════
# CONTENT CALENDAR LOGIC
# ═══════════════════════════════════════════════════════

def get_todays_modes():
    """Based on day of week, return which modes to run today."""
    dow = datetime.datetime.now().weekday()  # 0=Mon, 6=Sun
    # Monday
    if dow == 0:   return ["news", "educational"]
    # Tuesday
    elif dow == 1: return ["research", "blog"]
    # Wednesday
    elif dow == 2: return ["news", "seo"]
    # Thursday
    elif dow == 3: return ["educational", "research"]
    # Friday
    elif dow == 4: return ["news", "blog"]
    # Saturday
    elif dow == 5: return ["research", "seo"]
    # Sunday
    else:           return ["seo", "educational"]


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

def run():
    print("=" * 60)
    print("🌿 GhanaHemp.com Auto-Publisher v3 — FULL THROTTLE")
    print(f"⏰ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}")
    print("=" * 60)

    existing = get_existing_files()
    print(f"📁 {len(existing)} files already in repo")

    modes = get_todays_modes()
    print(f"📅 Today's content modes: {modes}")

    results = []

    for mode in modes:
        try:
            if mode == "news":
                ok = run_news_mode()
                results.append(("NEWS", ok))
                time.sleep(45)

            elif mode == "research":
                # Update existing list after potential news publish
                existing = get_existing_files()
                ok = run_research_mode(existing)
                results.append(("RESEARCH", ok))
                time.sleep(30)

            elif mode == "educational":
                existing = get_existing_files()
                ok = run_educational_mode(existing)
                results.append(("EDUCATIONAL", ok))
                time.sleep(30)

            elif mode == "blog":
                existing = get_existing_files()
                ok = run_blog_mode(existing)
                results.append(("BLOG", ok))
                time.sleep(30)

            elif mode == "seo":
                existing = get_existing_files()
                ok = run_seo_mode(existing)
                results.append(("SEO", ok))
                time.sleep(30)

        except Exception as e:
            print(f"  ⚠️  {mode} mode failed: {e}")
            results.append((mode.upper(), False))
            time.sleep(10)

    # If neither content piece published, always fall back to educational
    if not any(ok for _, ok in results):
        print("\n⚠️  All modes failed — fallback to educational")
        existing = get_existing_files()
        run_educational_mode(existing)

    # Always update sitemap at end of run
    try:
        update_sitemap()
    except Exception as e:
        print(f"  ⚠️  Sitemap update failed: {e}")

    print("\n" + "=" * 60)
    print("📊 RESULTS:")
    for mode, ok in results:
        print(f"  {'✅' if ok else '❌'} {mode}")
    print("=" * 60)


if __name__ == "__main__":
    run()
