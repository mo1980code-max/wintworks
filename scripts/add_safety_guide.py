#!/usr/bin/env python3
from pathlib import Path
import json,re
base=Path(__file__).resolve().parents[1]
s=(base/'sources.html').read_text()
title='How to Avoid Job and Visa Sponsorship Scams in 2026 | WintWorks'
desc='A practical checklist for verifying recruiters, employers, visa sponsors and remote-job offers, with official FTC and GOV.UK fraud guidance.'
s=re.sub(r'<title>.*?</title>',f'<title>{title}</title>',s,count=1)
s=re.sub(r'<meta name="description" content=".*?">',f'<meta name="description" content="{desc}">',s,count=1)
s=re.sub(r'<link rel="canonical" href=".*?">','<link rel="canonical" href="https://wintworks.com/job-scam-warning-signs.html">',s,count=1)
schema={"@context":"https://schema.org","@type":"Article","headline":"How to Avoid Job and Visa Sponsorship Scams in 2026","description":desc,"dateModified":"2026-08-23","author":{"@type":"Organization","name":"WintWorks Editorial Team"},"publisher":{"@type":"Organization","name":"WintWorks","url":"https://wintworks.com/"},"mainEntityOfPage":"https://wintworks.com/job-scam-warning-signs.html"}
# Insert schema before consent script.
s=s.replace('  <script src="js/consent.js"></script>',f'  <script type="application/ld+json">{json.dumps(schema,separators=(",",":"))}</script>\n  <script src="js/consent.js"></script>',1)
content='''<div class="page-card country-guide">
<article>
<h1>How to Avoid Job and Visa Sponsorship Scams in 2026</h1>
<p class="article-meta">Reviewed by <b>WintWorks Editorial Team</b> · Last reviewed August 23, 2026</p>
<p>International applicants are attractive targets for fake recruiters because a job offer may appear to solve employment, relocation and immigration at the same time. A professional logo, video interview or official-looking offer letter does not prove that a vacancy is genuine.</p>
<div class="guide-note"><b>The safest rule:</b> never pay to obtain a job offer or sponsorship certificate. Verify the vacancy through contact details you find independently—not through links or phone numbers supplied by the recruiter.</div>

<h2>Immediate warning signs</h2>
<ul>
<li>You receive an unexpected offer through WhatsApp, Telegram, SMS or a personal email account.</li>
<li>You are hired without a meaningful interview, skills assessment or discussion of your experience.</li>
<li>The job description is vague while the salary is unusually high.</li>
<li>The recruiter creates urgency and asks you to keep the offer confidential.</li>
<li>You are asked to pay for the job, sponsorship, a Certificate of Sponsorship, employer licence fees or “guaranteed” visa processing.</li>
<li>You receive a cheque for equipment and are instructed to return part of the money or buy from a named supplier.</li>
<li>You are asked to receive or transfer company money through your personal account.</li>
<li>The sender asks for passport, banking or identity documents before you have verified the employer.</li>
</ul>
<p>The US Federal Trade Commission states that honest employers do not ask candidates to pay to get a job and do not send a cheque before asking the recipient to return part of the money.</p>

<h2>A seven-step verification process</h2>
<ol>
<li><b>Open the company website yourself.</b> Type the domain or find it independently. Do not begin with the recruiter’s link.</li>
<li><b>Find the vacancy on the official careers page.</b> If it is absent, contact the company’s HR team using details published on that site.</li>
<li><b>Inspect the email domain carefully.</b> Look for misspellings, added hyphens or free email accounts. A correct-looking address is helpful but not conclusive.</li>
<li><b>Verify the legal organisation.</b> Use an official company register where available and compare its address, directors and trading status.</li>
<li><b>Verify immigration sponsorship separately.</b> For the UK, check the Home Office register of licensed sponsors. For the Netherlands, check the IND recognised-sponsor register.</li>
<li><b>Confirm who pays each fee.</b> Use the immigration authority’s website. In the UK, the sponsor licence fee, Certificate of Sponsorship fee and Immigration Skills Charge are employer costs.</li>
<li><b>Pause before sharing sensitive data.</b> A genuine employer may eventually require identity and payroll documents, but only after you verify the organisation and understand why the information is needed.</li>
</ol>

<h2>How to verify UK sponsorship</h2>
<p>Being listed as a licensed sponsor means an organisation has permission to sponsor eligible roles; it does not mean every vacancy qualifies. Confirm all three items:</p>
<ul>
<li>the exact employer appears in the official sponsor register;</li>
<li>the occupation and salary meet the current Skilled Worker rules; and</li>
<li>the employer confirms that it will issue a Certificate of Sponsorship for this vacancy.</li>
</ul>
<p>GOV.UK warns applicants not to pay the sponsor licence fee, Certificate of Sponsorship fee or Immigration Skills Charge. A request to pay those employer charges is a major warning sign.</p>

<h2>Remote-job and task scams</h2>
<p>Fake remote roles often begin with simple “optimisation,” rating or clicking tasks and may show a false balance growing in an app. The applicant is later asked to deposit money or cryptocurrency to unlock work or withdraw earnings. Do not pay to unlock wages, recharge a work account or complete a task.</p>

<h2>If you already sent money or documents</h2>
<ol>
<li>Stop contact and do not send another payment.</li>
<li>Contact your bank, card issuer or transfer provider immediately and ask whether the transaction can be reversed.</li>
<li>Change reused passwords and enable multi-factor authentication.</li>
<li>Keep messages, receipts, email headers, offer letters and account details as evidence.</li>
<li>Report the incident to your local police or fraud-reporting authority. US users can report to the FTC; UK users can use Action Fraud.</li>
<li>If passport or identity data was exposed, contact the issuing authority and follow its identity-theft guidance.</li>
</ol>

<h2>Official safety sources</h2>
<ul class="official-sources">
<li><a href="https://consumer.ftc.gov/articles/job-scams" target="_blank" rel="noopener">US Federal Trade Commission: job scams</a></li>
<li><a href="https://consumer.ftc.gov/consumer-alerts/2022/06/job-hunting-look-out-phony-job-postings" target="_blank" rel="noopener">FTC: verify phony job postings</a></li>
<li><a href="https://www.gov.uk/government/publications/applying-for-health-and-social-care-jobs-in-the-uk-from-abroad/part-1-applying-for-health-and-social-care-jobs-in-the-uk-from-abroad" target="_blank" rel="noopener">GOV.UK: recruitment scams and checking whether a job is real</a></li>
<li><a href="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers" target="_blank" rel="noopener">UK Home Office: register of licensed sponsors</a></li>
<li><a href="https://www.gov.uk/government/publications/frauds-tricks-and-scams/fraud-tricks-and-scams" target="_blank" rel="noopener">UK Visas and Immigration: fraud, tricks and scams</a></li>
<li><a href="https://ind.nl/en/public-register-recognised-sponsors" target="_blank" rel="noopener">Netherlands IND: public register of recognised sponsors</a></li>
</ul>
</article>
</div>'''
start=s.index('<div class="page-card">');end=s.index('\n\n\n</div></div>',start)
s=s[:start]+content+s[end:]
(base/'job-scam-warning-signs.html').write_text(s)
