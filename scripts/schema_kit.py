#!/usr/bin/env python3
"""
WintWorks — shared JSON-LD (schema.org) builders.

One place that defines the site's structured-data vocabulary so the static
pages, the reviewed-guide generator (`update_guides.py`) and the job-page
generator all emit the same entities, with the same @ids, publisher logo and
breadcrumb shape. Google merges same-@id nodes across a page, so keeping the
identity stable matters more than repeating every field.

Import:
    from schema_kit import (BASE_URL, OG_IMAGE, ORGANIZATION_ID, WEBSITE_ID,
                            publisher_node, website_node, webpage_node,
                            article_node, faq_node, breadcrumb_node,
                            item_list_node, application_node, ld_json_block,
                            normalize_graph)
"""
from __future__ import annotations

import json

BASE_URL = "https://wintworks.com"
OG_IMAGE = f"{BASE_URL}/assets/wintworks-og-banner.png"
ORGANIZATION_ID = f"{BASE_URL}/#organization"
WEBSITE_ID = f"{BASE_URL}/#website"
EDITORIAL_TEAM = "WintWorks Editorial Team"

# Google shows the publisher logo in Article rich results — keep it square-ish
# and stable. The banner doubles as our logo asset.
LOGO = {
    "@type": "ImageObject",
    "url": OG_IMAGE,
    "width": 1200,
    "height": 630,
}


def publisher_node() -> dict:
    """The publishing organization, referenced by @id everywhere else."""
    return {
        "@type": "Organization",
        "@id": ORGANIZATION_ID,
        "name": "WintWorks",
        "url": f"{BASE_URL}/",
        "logo": dict(LOGO),
    }


def website_node(with_search: bool = False) -> dict:
    node = {
        "@type": "WebSite",
        "@id": WEBSITE_ID,
        "url": f"{BASE_URL}/",
        "name": "WintWorks",
        "description": ("Job discovery platform aggregating live listings from the United States, "
                        "major European markets and worldwide remote sources."),
        "inLanguage": "en",
        "publisher": {"@id": ORGANIZATION_ID},
    }
    if with_search:
        node["potentialAction"] = {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{BASE_URL}/?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        }
    return node


def webpage_node(url: str, name: str, description: str = "",
                 page_type: str = "WebPage", date_modified: str | None = None) -> dict:
    node = {
        "@type": page_type,
        "@id": url + "#webpage",
        "url": url,
        "name": name,
        "isPartOf": {"@id": WEBSITE_ID},
        "inLanguage": "en",
        "publisher": {"@id": ORGANIZATION_ID},
    }
    if description:
        node["description"] = description
    if date_modified:
        node["dateModified"] = date_modified
    return node


def article_node(url: str, headline: str, description: str = "",
                 date_published: str | None = None,
                 date_modified: str | None = None,
                 author: str = EDITORIAL_TEAM) -> dict:
    node = {
        "@type": "Article",
        "@id": url + "#article",
        "headline": headline,
        "mainEntityOfPage": {"@id": url + "#webpage"},
        "author": {"@type": "Organization", "name": author},
        "publisher": {"@id": ORGANIZATION_ID},
        "isPartOf": {"@id": WEBSITE_ID},
        "inLanguage": "en",
    }
    if description:
        node["description"] = description
    if date_published:
        node["datePublished"] = date_published
    if date_modified:
        node["dateModified"] = date_modified
    return node


def faq_node(faqs: list[tuple[str, str]]) -> dict:
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }


def breadcrumb_node(trail: list[tuple[str, str | None]], page_url: str = "") -> dict:
    """trail: [(name, absolute url or None), …] — the last item may be text-only."""
    items = []
    for i, (name, url) in enumerate(trail, 1):
        entry: dict = {"@type": "ListItem", "position": i, "name": name}
        if url:
            entry["item"] = url
        items.append(entry)
    anchor = page_url or trail[-1][1] or BASE_URL
    return {"@type": "BreadcrumbList", "@id": anchor + "#breadcrumb",
            "itemListElement": items}


def item_list_node(items: list[tuple[str, str]], name: str = "") -> dict:
    """items: [(url, name), …] → ItemList with absolute URLs."""
    node = {
        "@type": "ItemList",
        "numberOfItems": len(items),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "url": url, "name": label}
            for i, (url, label) in enumerate(items, 1)
        ],
    }
    if name:
        node["name"] = name
    return node


def application_node(url: str, name: str, description: str = "") -> dict:
    return {
        "@type": "WebApplication",
        "@id": url + "#app",
        "name": name,
        "url": url,
        "description": description,
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Any (web browser)",
        "browserRequirements": "Requires JavaScript",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "publisher": {"@id": ORGANIZATION_ID},
        "isPartOf": {"@id": WEBSITE_ID},
    }


def normalize_graph(nodes: list[dict]) -> list[dict]:
    """Merge into one @graph list: keep one node per (@type, @id) pair, preferring
    the richer node (more keys) so scalar stubs cannot overwrite full entities."""
    best: dict[tuple, dict] = {}
    order: list[tuple] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        t = node.get("@type")
        t = tuple(t) if isinstance(t, list) else t
        key = (t, node.get("@id"))
        if key not in best:
            best[key] = node
            order.append(key)
        elif len(json.dumps(node)) > len(json.dumps(best[key])):
            best[key] = node
    # a node with an @id supersedes an anonymous node of the same type
    named_types = {(t, i) for (t, i) in order if i}
    out = []
    for key in order:
        t, ident = key
        if not ident and (t, None) in best and any(k[0] == t and k[1] for k in named_types):
            continue
        out.append(best[key])
    return out


def ld_json_block(nodes: list[dict], indent: int = 0) -> str:
    graph = normalize_graph(nodes)
    payload = {"@context": "https://schema.org", "@graph": graph}
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    pad = " " * indent
    return f'{pad}<script type="application/ld+json">\n{pad}{body}\n{pad}</script>'


def parse_graph(html: str) -> list[dict]:
    """All schema.org nodes already present in a page (flattening @graph)."""
    import re

    nodes: list[dict] = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        for obj in data if isinstance(data, list) else [data]:
            if isinstance(obj, dict) and "@graph" in obj:
                nodes.extend(x for x in obj["@graph"] if isinstance(x, dict))
            elif isinstance(obj, dict):
                nodes.append(obj)
    return nodes
