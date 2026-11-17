#!/usr/bin/env python3
"""Unpack a "__bundler" single-file HTML into editable per-page folders.

Usage: ./decode.py "WiscoHumanoids Sponsorship Packet.html" [out_dir] [--raw]

By default each page is flattened to static HTML: the dc-runtime <x-dc>/<helmet>
wrappers and the React/runtime scripts are removed, leaving plain HTML + CSS.
Pass --raw to keep the original runtime-dependent pages and their JS files.
"""
import base64, gzip, json, os, re, sys

args = [a for a in sys.argv[1:] if a != '--raw']
raw = '--raw' in sys.argv
if not args:
    sys.exit(__doc__)
src = args[0]
out = args[1] if len(args) > 1 else 'decoded'

def flatten(html):
    """Drop the dc-runtime wrappers; the pages' Component classes are no-ops."""
    # Hoist <helmet> contents (fonts, <style>) into the real <head>.
    helmet = re.search(r'<helmet>(.*?)</helmet>', html, re.S)
    html = re.sub(r'<helmet>.*?</helmet>\s*', '', html, flags=re.S)
    if helmet:
        html = html.replace('</head>', helmet.group(1) + '</head>', 1)
    html = re.sub(r'<script\b[^>]*>.*?</script>\s*', '', html, flags=re.S)  # runtime + Component
    html = re.sub(r'</?x-dc>\s*', '', html)
    # The runtime stores table tags as <sc-raw-table> etc. (HTML parsers mangle
    # <tr> outside a table) and camelCase attrs as sc-camel-view-box; undo both.
    html = re.sub(r'(</?)sc-raw-([a-z]+)', r'\1\2', html)
    return re.sub(r'\bsc-camel-([a-z-]+)=',
                  lambda m: re.sub(r'-(\w)', lambda c: c.group(1).upper(), m.group(1)) + '=', html)
EXT = {'text/html': 'html', 'text/css': 'css', 'text/javascript': 'js',
       'application/javascript': 'js', 'image/png': 'png', 'image/jpeg': 'jpg',
       'image/svg+xml': 'svg', 'image/webp': 'webp', 'font/woff2': 'woff2',
       'font/woff': 'woff', 'font/ttf': 'ttf'}

def block(text, kind):
    m = re.search(rf'<script type="__bundler/{kind}">\s*(.*?)\s*</script>', text, re.S)
    return json.loads(m.group(1)) if m else None

def unpack(entry):
    raw = base64.b64decode(entry['data'])
    return gzip.decompress(raw) if entry.get('compressed') else raw

# Level 1: the outer file holds one compressed HTML document per page.
outer = open(src, encoding='utf-8').read()
manifest, order = block(outer, 'manifest'), block(outer, 'page_order')
slugs = ["1-cover", "2-letter-about", "3-needs-timeline", "4-budget-sponsorship"]

for i, uuid in enumerate(order):
    slug = slugs[i] if i < len(slugs) else f"page-{i+1}"
    page = unpack(manifest[uuid]).decode('utf-8')

    # Level 2: each page is itself a bundle (template + images/fonts/scripts).
    inner, template = block(page, 'manifest'), block(page, 'template')
    d = os.path.join(out, slug)
    os.makedirs(d, exist_ok=True)

    if not raw:
        template = flatten(template)

    written = 0
    for u, entry in inner.items():
        if u not in template:      # e.g. the runtime JS, once flattened
            continue
        name = f"{u[:8]}.{EXT.get(entry['mime'], entry['mime'].split('/')[-1])}"
        open(os.path.join(d, name), 'wb').write(unpack(entry))
        template = template.replace(u, name)   # UUID reference -> relative file
        written += 1

    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(template)
    print(f"{slug}: {written} assets")

# ./decode.py "WiscoHumanoids Sponsorship Packet.html" decoded       # flattened (default)
# ./decode.py "WiscoHumanoids Sponsorship Packet.html" decoded --raw  # original runtime-based pages
