#!/usr/bin/env python3
"""Replace five country guide articles with reviewed 2026 content and official sources."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]
REVIEWED = "August 23, 2026"

GUIDES = {
"jobs-in-germany.html": {
"title": "Jobs in Germany for Foreigners 2026: Visas, Salaries & How to Apply | WintWorks",
"description": "Reviewed 2026 guide to jobs in Germany for foreign applicants: EU Blue Card thresholds, Opportunity Card, indicative salaries, application steps and official sources.",
"h1": "Jobs in Germany for Foreigners 2026: Visas, Salaries & How to Apply",
"intro": "Germany recruits international professionals across technology, engineering, healthcare, scientific research and skilled trades. Your immigration route depends on your nationality, qualifications, occupation and salary—not simply on whether an employer calls a role “sponsored.”",
"body": r'''
<h2>Who needs a work visa?</h2>
<ul>
<li><b>EU, EEA and Swiss citizens:</b> can work in Germany without an employment visa. Residence-registration rules still apply after moving.</li>
<li><b>Most non-EU citizens:</b> need an appropriate visa or residence permit before starting work. Common routes include the EU Blue Card, the work visa for qualified professionals and the visa for professionally experienced workers.</li>
</ul>
<p>Use the official <a href="https://www.make-it-in-germany.com/en/visa-residence/types" target="_blank" rel="noopener">Make it in Germany visa overview</a> to identify the correct route for your circumstances.</p>

<h2>EU Blue Card thresholds for 2026</h2>
<p>For applications in 2026, the official gross annual salary threshold is:</p>
<ul>
<li><b>€50,700</b> for regular occupations.</li>
<li><b>€45,934.20</b> for bottleneck professions and qualifying recent graduates. Eligible IT specialists may also qualify at the lower threshold when they meet the experience rules.</li>
</ul>
<p>A recognised or comparable higher-education qualification, or another qualifying tertiary credential, is normally required. The job must also meet the Blue Card rules. Read the <a href="https://www.make-it-in-germany.com/fileadmin/1_Rebrush_2022/a_Fachkraefte/PDF-Dateien/3_Visum_u_Aufenthalt/Visagrafik_EN/Visum_Blaue_Karte_EN.pdf" target="_blank" rel="noopener">official 2026 EU Blue Card guide</a>.</p>

<h2>Opportunity Card (Chancenkarte)</h2>
<p>The Opportunity Card replaced the former general jobseeker-visa route. It is intended for eligible third-country nationals seeking qualified employment. The initial card can be issued for up to <b>12 months</b>; applicants must meet either the recognised-qualification route or the points route and show sufficient funds. The official 2026 financial-security guidance generally uses <b>€1,091 net per month</b>. Limited secondary employment of up to 20 hours per week is permitted while searching.</p>
<p>Check eligibility on the official <a href="https://www.make-it-in-germany.com/en/visa-residence/types/job-search-opportunity-card" target="_blank" rel="noopener">Opportunity Card page</a>.</p>

<h2>In-demand fields and indicative salaries</h2>
<ul>
<li><b>Software and IT:</b> roughly €55,000–€85,000 gross per year.</li>
<li><b>Engineering:</b> roughly €52,000–€75,000.</li>
<li><b>Nursing:</b> roughly €40,000–€55,000; professional recognition and German are usually required.</li>
<li><b>Finance and accounting:</b> roughly €45,000–€65,000.</li>
<li><b>Skilled trades and logistics:</b> pay varies widely by qualification, collective agreement and region.</li>
</ul>
<p class="guide-note"><b>Salary note:</b> these are broad market guides, not official averages or visa guarantees. Check the exact advertised salary, weekly hours and applicable collective agreement. Visa salary rules are separate and may change annually.</p>

<h2>Application checklist</h2>
<ol>
<li>Confirm whether your profession is regulated and whether your qualification needs recognition.</li>
<li>Prepare a concise reverse-chronological CV and relevant certificates. A photo is optional, not mandatory.</li>
<li>State your German level honestly. English-only roles exist, but healthcare and customer-facing work usually require German.</li>
<li>Confirm the visa route and salary threshold before accepting an offer.</li>
<li>Apply through the employer or verified source page and never pay for an employment offer.</li>
</ol>
<p><a class="btn" href="/?country=Germany">Browse current Germany jobs →</a></p>

<h2>Official sources</h2>
<ul class="official-sources">
<li><a href="https://www.make-it-in-germany.com/en/visa-residence/types" target="_blank" rel="noopener">Federal Government: visa and residence types</a></li>
<li><a href="https://www.make-it-in-germany.com/en/visa-residence/types/job-search-opportunity-card" target="_blank" rel="noopener">Federal Government: Opportunity Card</a></li>
<li><a href="https://www.make-it-in-germany.com/fileadmin/1_Rebrush_2022/a_Fachkraefte/PDF-Dateien/3_Visum_u_Aufenthalt/Visagrafik_EN/Visum_Blaue_Karte_EN.pdf" target="_blank" rel="noopener">Federal Government: EU Blue Card requirements for 2026</a></li>
</ul>''',
"faqs": [
("What are Germany’s EU Blue Card salary thresholds in 2026?", "The official 2026 thresholds are €50,700 gross annually for regular occupations and €45,934.20 for qualifying bottleneck professions and recent graduates. Other eligibility conditions also apply."),
("Can I enter Germany to look for work?", "Eligible third-country nationals may use the Opportunity Card, generally issued initially for up to 12 months. Qualification, points and financial-security requirements apply."),
("Can I work in Germany using only English?", "Some international technology, research and startup roles use English. German is usually important or mandatory in regulated healthcare, public-facing and many local-market roles."),
]},
"jobs-in-united-kingdom.html": {
"title": "UK Visa Sponsorship Jobs 2026: Skilled Worker Requirements & How to Apply | WintWorks",
"description": "Reviewed 2026 guide to UK visa sponsorship jobs: Skilled Worker salary and English rules, licensed sponsors, Health and Care route and official GOV.UK sources.",
"h1": "UK Visa Sponsorship Jobs 2026: Skilled Worker Requirements & How to Apply",
"intro": "A UK employer can sponsor an overseas applicant only when it holds the correct sponsor licence, the job is eligible and the applicant meets the salary, skill, English and other immigration requirements. A vacancy mentioning “visa sponsorship” is not by itself a guarantee of eligibility.",
"body": r'''
<h2>Skilled Worker requirements in 2026</h2>
<p>For a new Skilled Worker application, you normally need a genuine eligible job, a Certificate of Sponsorship from a licensed employer, the applicable salary and the required English level. For Certificates of Sponsorship assigned under the current rules, the standard salary option normally requires the higher of:</p>
<ul>
<li><b>£41,700 per year</b>; and</li>
<li>the full official <b>going rate</b> for the occupation code.</li>
</ul>
<p>Different thresholds can apply to new entrants, relevant PhD holders, jobs on specified lists, health and education occupations and transitional cases. Do not treat £41,700 as the rule for every applicant. Check the <a href="https://www.gov.uk/government/publications/sponsor-a-skilled-worker/workers-and-temporary-workers-sponsor-a-skilled-worker-accessible" target="_blank" rel="noopener">current sponsor guidance</a>.</p>

<h2>English and skill level</h2>
<p>New applicants normally need English at <b>CEFR B2</b> in reading, writing, speaking and listening. B1 is retained for certain applicants whose most recent Skilled Worker permission was granted under the rules before 8 January 2026. Most newly sponsored jobs must be at graduate skill level (RQF 6), with limited exceptions for occupations on the applicable shortage lists and transitional cases.</p>

<h2>Health and Care Worker route</h2>
<p>Eligible healthcare professionals can use the Health and Care Worker sub-route, which has occupation-specific salary rules. Under current rules, new overseas applications for care worker and senior care worker jobs are no longer accepted; limited in-country switching provisions remain. Nurses, doctors and other eligible health professionals are governed by separate occupation and pay rules.</p>

<h2>How to verify sponsorship</h2>
<ol>
<li>Search the employer in the official <a href="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers" target="_blank" rel="noopener">Register of licensed sponsors</a>.</li>
<li>Confirm the occupation code, going rate and whether the vacancy is genuinely open to sponsorship.</li>
<li>Ask whether the employer will issue a Certificate of Sponsorship for this specific role.</li>
<li>Never pay an employer or recruiter for a job offer or Certificate of Sponsorship.</li>
</ol>

<h2>Indicative salary ranges</h2>
<ul>
<li><b>Software:</b> approximately £45,000–£95,000, with large variation by city and seniority.</li>
<li><b>Finance:</b> approximately £45,000–£120,000+.</li>
<li><b>Nursing:</b> usually follows NHS or employer pay scales.</li>
<li><b>Marketing:</b> approximately £30,000–£60,000.</li>
</ul>
<p class="guide-note"><b>Important:</b> a market salary estimate is not the immigration going rate. Always check the official occupation-code table and current rules.</p>
<p><a class="btn" href="/?country=United%20Kingdom">Browse current UK jobs →</a></p>

<h2>Official sources</h2>
<ul class="official-sources">
<li><a href="https://www.gov.uk/skilled-worker-visa" target="_blank" rel="noopener">GOV.UK: Skilled Worker visa</a></li>
<li><a href="https://www.gov.uk/government/publications/sponsor-a-skilled-worker/workers-and-temporary-workers-sponsor-a-skilled-worker-accessible" target="_blank" rel="noopener">Home Office: sponsor a Skilled Worker</a></li>
<li><a href="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers" target="_blank" rel="noopener">Home Office: register of licensed sponsors</a></li>
</ul>''',
"faqs": [
("What is the standard Skilled Worker salary threshold in 2026?", "Under the standard salary option, the role normally must pay at least £41,700 and the full going rate for its occupation code, whichever is higher. Different options and exceptions have different thresholds."),
("What English level is required for a new Skilled Worker applicant?", "New applicants normally need CEFR B2 in all four components. Certain workers previously granted permission under the pre-8 January 2026 rules may remain subject to B1."),
("Can overseas applicants still be sponsored as care workers?", "New overseas applications for care worker and senior care worker roles are no longer accepted under the current route. Limited in-country switching rules may apply."),
]},
"jobs-in-netherlands.html": {
"title": "Jobs in the Netherlands for English Speakers 2026: Salaries, Visas & Top Cities | WintWorks",
"description": "Reviewed 2026 guide to jobs in the Netherlands: Highly Skilled Migrant salary thresholds, recognised sponsors, Expat Scheme, cities and official sources.",
"h1": "Jobs in the Netherlands for English Speakers 2026: Salaries, Visas & Top Cities",
"intro": "The Netherlands has a large international job market, but non-EU applicants should distinguish between an English-speaking vacancy and a role that qualifies for immigration sponsorship. The main Highly Skilled Migrant route requires an IND-recognised sponsor and a salary that meets the current threshold.",
"body": r'''
<h2>Who needs sponsorship?</h2>
<ul>
<li><b>EU, EEA and Swiss citizens:</b> can work without a Dutch work permit, although municipal registration and a BSN may be required.</li>
<li><b>Most non-EU citizens:</b> require an appropriate residence/work route. For the Highly Skilled Migrant scheme, the employer normally must be recognised by the IND.</li>
</ul>

<h2>Highly Skilled Migrant salary thresholds for 2026</h2>
<p>The official gross monthly amounts, excluding holiday allowance, are:</p>
<ul>
<li><b>€5,942</b> for applicants aged 30 or older.</li>
<li><b>€4,357</b> for applicants younger than 30.</li>
<li><b>€3,122</b> under the reduced criterion for qualifying recent graduates and orientation-year cases.</li>
</ul>
<p>The salary must also be market-conform. Thresholds are indexed annually and the applicable amount can depend on age, application date and change of employer. Verify the figure on the <a href="https://ind.nl/en/required-amounts-income-requirements" target="_blank" rel="noopener">IND required-amounts page</a>.</p>

<h2>Recognised sponsors and processing</h2>
<p>Only an IND-recognised sponsor normally submits a Highly Skilled Migrant application. Recognised sponsors have access to an accelerated process; the IND describes typical processing as taking a couple of weeks when requirements and documents are complete. Confirm the employer in the official public register before relying on a sponsorship claim.</p>

<h2>The 30% Expat Scheme</h2>
<p>The Expat Scheme is a conditional tax facility, not an automatic benefit and not a visa. In 2026, the normal expertise salary test is more than <b>€48,013</b> excluding the tax-free allowance; a lower test of more than <b>€36,497</b> applies to qualifying employees under 30 with an eligible master’s degree. The employee must also meet recruitment-from-abroad and distance conditions. A decision may last up to five years, and the employer is not obliged to provide the maximum allowance.</p>
<p>Check the <a href="https://www.belastingdienst.nl/wps/wcm/connect/en/individuals/content/coming-to-work-in-the-netherlands-30-percent-facility" target="_blank" rel="noopener">Dutch Tax Administration guidance</a>.</p>

<h2>Top employment cities</h2>
<ul>
<li><b>Amsterdam:</b> technology, finance, media and international headquarters.</li>
<li><b>Eindhoven:</b> semiconductors, embedded systems and engineering.</li>
<li><b>Rotterdam:</b> port operations, logistics, energy and engineering.</li>
<li><b>Utrecht and The Hague:</b> technology, professional services, government and international organisations.</li>
</ul>

<h2>Indicative salaries</h2>
<p>Broad gross annual guides: software €50,000–€80,000; data €45,000–€70,000; design €42,000–€65,000; logistics €35,000–€55,000. These are market estimates, not IND thresholds, and vary by seniority, city and holiday allowance.</p>
<p><a class="btn" href="/?country=Netherlands">Browse current Netherlands jobs →</a></p>

<h2>Official sources</h2>
<ul class="official-sources">
<li><a href="https://ind.nl/en/required-amounts-income-requirements" target="_blank" rel="noopener">IND: required income amounts for 2026</a></li>
<li><a href="https://ind.nl/en/about-us/background-articles/national-highly-skilled-migrant-scheme" target="_blank" rel="noopener">IND: national Highly Skilled Migrant scheme</a></li>
<li><a href="https://ind.nl/en/public-register-recognised-sponsors" target="_blank" rel="noopener">IND: public register of recognised sponsors</a></li>
<li><a href="https://www.belastingdienst.nl/wps/wcm/connect/en/individuals/content/coming-to-work-in-the-netherlands-30-percent-facility" target="_blank" rel="noopener">Dutch Tax Administration: Expat Scheme</a></li>
</ul>''',
"faqs": [
("What are the Highly Skilled Migrant salary thresholds in 2026?", "The gross monthly amounts excluding holiday allowance are €5,942 for applicants aged 30 or older, €4,357 for those under 30, and €3,122 for qualifying reduced-criterion cases."),
("Is the 30% Expat Scheme automatic?", "No. It is a conditional tax facility, not a visa. The employee and employer apply, eligibility tests apply, and the employer is not required to grant the maximum allowance."),
("Does the Netherlands have a general digital nomad visa?", "The Netherlands does not offer a general residence route formally called a digital nomad visa. Remote workers must qualify under an existing residence and work category."),
]},
"jobs-in-spain.html": {
"title": "Jobs in Spain for Foreigners 2026: Work Visas, Salaries & Hiring Cities | WintWorks",
"description": "Reviewed 2026 guide to jobs in Spain: local work permits, Digital Nomad Visa limits, salaries, hiring cities and official government sources.",
"h1": "Jobs in Spain for Foreigners 2026: Work Visas, Salaries & Hiring Cities",
"intro": "Spain offers local employment and international-remote-work routes, but they are legally different. A Digital Nomad Visa does not generally authorise a foreign employee to take an ordinary job with a Spanish employer; applicants seeking local employment normally need the relevant work authorisation.",
"body": r'''
<h2>Local employment in Spain</h2>
<ul>
<li><b>EU, EEA and Swiss citizens:</b> can work under free-movement rules, subject to registration requirements.</li>
<li><b>Non-EU citizens:</b> usually need an employer-supported work and residence authorisation or another route that independently grants work rights.</li>
</ul>
<p>Regulated professions may require recognition of qualifications. Always verify the exact authorisation before accepting or starting work.</p>

<h2>Spain’s international teleworker route</h2>
<p>The route often called the Digital Nomad Visa is officially for <b>third-country nationals working remotely for companies established outside Spain</b> using computer and telecommunications systems.</p>
<ul>
<li>An employee may work only for the foreign company supporting the application.</li>
<li>A self-employed professional may have Spanish clients only when the Spanish activity is professional—not employment—and does not exceed <b>20%</b> of total activity.</li>
<li>The applicant must show an existing professional or employment relationship and sufficient resources. The main applicant’s required resources are <b>200% of the current Spanish minimum wage (SMI) per month</b>.</li>
<li>Spanish Social Security registration is generally required unless valid international social-security coverage can be imported under an applicable agreement.</li>
<li>Travel insurance is not sufficient; qualifying public coverage or private health insurance is required where applicable.</li>
</ul>
<p>Read the official <a href="https://www.inclusion.gob.es/en/web/unidadgrandesempresas/teletrabajadores" target="_blank" rel="noopener">UGE international teleworker guidance</a>.</p>

<h2>In-demand fields and cities</h2>
<ul>
<li><b>Madrid:</b> corporate services, finance, technology and consulting.</li>
<li><b>Barcelona:</b> technology, product, design, multilingual sales and support.</li>
<li><b>Valencia and Málaga:</b> growing technology and international-service sectors.</li>
<li><b>Other regions:</b> tourism, logistics, renewable energy, manufacturing and agriculture, often with stronger Spanish-language requirements.</li>
</ul>

<h2>Indicative salaries</h2>
<p>Broad gross annual guides: software €35,000–€60,000; customer support €22,000–€32,000; design €28,000–€45,000; sales €30,000–€55,000. These are market estimates, not immigration thresholds. Housing costs and salaries vary significantly by city.</p>

<h2>Application checklist</h2>
<ol>
<li>Decide whether you are seeking local Spanish employment or continuing foreign remote work.</li>
<li>State your work-authorisation position and Spanish level clearly.</li>
<li>Verify the employer, contract, salary and Social Security arrangements.</li>
<li>Use the relevant government route; do not describe a normal Spanish job as digital-nomad work.</li>
</ol>
<p><a class="btn" href="/?country=Spain">Browse current Spain jobs →</a></p>

<h2>Official sources</h2>
<ul class="official-sources">
<li><a href="https://www.inclusion.gob.es/en/web/unidadgrandesempresas/teletrabajadores" target="_blank" rel="noopener">Ministry of Inclusion, UGE: international teleworkers</a></li>
<li><a href="https://www.inclusion.gob.es/documents/d/unidadgrandesempresas/digital-nomad-faqs-english" target="_blank" rel="noopener">UGE: international teleworker FAQ in English</a></li>
</ul>''',
"faqs": [
("Does Spain’s Digital Nomad Visa allow a normal job with a Spanish employer?", "Generally no. The route is designed for third-country nationals working remotely for companies outside Spain. Ordinary local employment normally requires the appropriate work authorisation."),
("What income must an international teleworker show?", "The main applicant must show resources equal to 200% of the current Spanish minimum wage per month. Additional amounts apply for family members."),
("Can a self-employed digital nomad have Spanish clients?", "Yes, but Spanish activity must be a professional rather than employment relationship and cannot exceed 20% of total professional activity."),
]},
"jobs-in-france.html": {
"title": "Jobs in France for Foreigners 2026: Work Permits, Salaries & In-Demand Jobs | WintWorks",
"description": "Reviewed 2026 guide to jobs in France: standard work authorisation, Talent Passport and EU Blue Card rules, salaries, sectors and official France-Visas sources.",
"h1": "Jobs in France for Foreigners 2026: Work Permits, Salaries & In-Demand Jobs",
"intro": "Foreign applicants can work in France through several routes. The correct route depends on nationality, contract length, occupation, qualifications and salary. “Talent Passport” is an umbrella covering multiple categories; it is not one visa with a single set of requirements.",
"body": r'''
<h2>Who needs work authorisation?</h2>
<ul>
<li><b>EU, EEA and Swiss citizens:</b> generally do not need a work permit.</li>
<li><b>Most non-EU employees:</b> need the appropriate visa/residence status and, unless exempt, prior work authorisation requested by the employer.</li>
</ul>
<p>For ordinary recruitment, the French employer normally requests work authorisation before the visa application. Permanent contracts generally lead to a long-stay route marked <i>salarié</i>; fixed-term contracts generally use <i>travailleur temporaire</i>. Check the official <a href="https://france-visas.gouv.fr/en/activite-salariee" target="_blank" rel="noopener">France-Visas salaried-employment page</a>.</p>

<h2>Talent Passport and EU Blue Card</h2>
<p>The international-talent framework contains separate categories for qualified employees, innovative-company employees, researchers, intra-group assignments, entrepreneurs, artists and others.</p>
<p>For the <b>highly qualified employee / EU Blue Card</b> category, the official rules state that:</p>
<ul>
<li>the employment contract must last at least one year;</li>
<li>the applicant must have at least three years of qualifying higher education or five years of comparable professional experience; and</li>
<li>the salary must be at least 1.5 times the official average gross reference salary—currently <b>€59,373</b> since 21 August 2025.</li>
</ul>
<p>The resulting permit can follow the contract duration up to four years. Other Talent Passport categories have different salary and evidence requirements. See <a href="https://france-visas.gouv.fr/en/talents-internationaux-et-attractivite-economique" target="_blank" rel="noopener">France-Visas international talents</a>.</p>

<h2>In-demand sectors and language</h2>
<ul>
<li><b>Technology and data:</b> strongest concentration in Paris, with additional hubs in Lyon, Nantes and other cities.</li>
<li><b>Aerospace and engineering:</b> major activity around Toulouse and industrial regions.</li>
<li><b>Finance, consulting, luxury and international sales:</b> concentrated around Paris.</li>
<li><b>Healthcare:</b> demand exists, but regulated professions require recognition and usually strong French.</li>
</ul>
<p>English-language positions exist in international organisations and teams, but French materially expands the available market. Avoid claims that a bilingual CV guarantees or doubles the response rate.</p>

<h2>Indicative salaries</h2>
<p>Broad gross annual guides: software €45,000–€75,000; engineering €42,000–€65,000; finance €45,000–€80,000; customer support €28,000–€38,000. These are market estimates, not official visa thresholds, and Paris compensation and housing costs are often higher.</p>

<h2>Application checklist</h2>
<ol>
<li>Check whether your profession is regulated and whether your qualifications need recognition.</li>
<li>Identify the correct visa category before presenting yourself as eligible for a Talent Passport.</li>
<li>Prepare a clear CV in French or English according to the vacancy language.</li>
<li>Confirm who will request work authorisation and when.</li>
<li>Verify the contract, salary and source before sharing sensitive documents.</li>
</ol>
<p><a class="btn" href="/?country=France">Browse current France jobs →</a></p>

<h2>Official sources</h2>
<ul class="official-sources">
<li><a href="https://france-visas.gouv.fr/en/activite-salariee" target="_blank" rel="noopener">France-Visas: salaried employment</a></li>
<li><a href="https://france-visas.gouv.fr/en/talents-internationaux-et-attractivite-economique" target="_blank" rel="noopener">France-Visas: international talents and EU Blue Card</a></li>
<li><a href="https://france-visas.gouv.fr/en/motif-professionnel" target="_blank" rel="noopener">France-Visas: professional-purpose routes</a></li>
</ul>''',
"faqs": [
("Is the Talent Passport one visa with one salary threshold?", "No. It is a framework containing multiple categories with different contract, qualification, salary and evidence requirements."),
("What is the current French EU Blue Card reference salary?", "For the highly qualified employee category, the salary must be at least 1.5 times the official average gross reference salary, stated by France-Visas as €59,373 since 21 August 2025."),
("Does a normal French employer need prior work authorisation?", "For most non-EU hires using the ordinary salaried route, the employer must obtain work authorisation before the worker submits the visa application, unless an exemption applies."),
]},
}


def faq_schema(filename, title, description, faqs):
    url = "https://wintworks.com/" + filename
    graph = [
        {
            "@type": "Article",
            "headline": title.split(" | ")[0],
            "description": description,
            "mainEntityOfPage": url,
            "dateModified": "2026-08-23",
            "author": {"@type": "Organization", "name": "WintWorks Editorial Team"},
            "publisher": {"@type": "Organization", "name": "WintWorks", "url": "https://wintworks.com/"},
        },
        {
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faqs
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))

for filename, g in GUIDES.items():
    p = BASE / filename
    s = p.read_text()
    # Metadata
    import re
    s = re.sub(r"<title>.*?</title>", f"<title>{g['title']}</title>", s, count=1, flags=re.S)
    s = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{g["description"]}">', s, count=1, flags=re.S)
    s = re.sub(r'<meta property="og:title" content=".*?">', f'<meta property="og:title" content="{g["title"].split(" | ")[0]}">', s, count=1, flags=re.S)
    s = re.sub(r'<meta property="og:description" content=".*?">', f'<meta property="og:description" content="{g["description"]}">', s, count=1, flags=re.S)
    schema = faq_schema(filename, g['title'], g['description'], g['faqs'])
    s = re.sub(r'<script type="application/ld\+json">.*?</script>', f'<script type="application/ld+json">\n{schema}\n</script>', s, count=1, flags=re.S)

    # Article card only (leave CTA outside card and shared shell/footer intact)
    marker = '<div class="page-card">'
    start = s.index(marker)
    end = s.index('\n</div>\n\n<div class="price-card hot"', start)
    faq_html = '<h2>Frequently asked questions</h2>\n' + ''.join(
        f'<h3>{q}</h3><p>{a}</p>' for q, a in g['faqs']
    )
    card = f'''<div class="page-card country-guide">
<article>
<h1>{g['h1']}</h1>
<p class="article-meta">Reviewed by <b>WintWorks Editorial Team</b> · Last reviewed {REVIEWED}</p>
<p>{g['intro']}</p>
<div class="guide-note"><b>Immigration information changes frequently.</b> This guide links to official government sources and is general information, not legal advice. Confirm the requirements that apply on your application date.</div>
{g['body']}
{faq_html}
</article>
</div>'''
    s = s[:start] + card + s[end+len('\n</div>'):]
    p.write_text(s)
    print("updated", filename)
