import re

# Source:  https://stackoverflow.com/a/63529754
def find_md_links(md):
    """Returns dict of links in markdown:
    'regular': [foo](some.url)
    'footnotes': [foo][3]
    
    [3]: some.url
    """
    # https://stackoverflow.com/a/30738268/2755116

    INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    FOOTNOTE_LINK_TEXT_RE = re.compile(r'\[([^\]]+)\]\[(\d+)\]')
    FOOTNOTE_LINK_URL_RE = re.compile(r'\[(\d+)\]:\s+(\S+)')

    links = list(INLINE_LINK_RE.findall(md))
    footnote_links = dict(FOOTNOTE_LINK_TEXT_RE.findall(md))
    footnote_urls = dict(FOOTNOTE_LINK_URL_RE.findall(md))

    footnotes_linking = []
        
    for key in footnote_links.keys():
        footnotes_linking.append((footnote_links[key], footnote_urls[footnote_links[key]]))

    return {'regular': links, 'footnotes': footnotes_linking}

def replace_md_links(md, f):
    """Replace links url to f(url)"""
    
    links = find_md_links(md)
    newmd = md

    for r in links['regular']:
        newmd = newmd.replace(f"({r[1]})", f(r[1])).replace(f"[{r[0]}]", r[0])

    for r in links['footnotes']:
        newmd = newmd.replace(f"({(r[1])})", f(r[1]))
    
    return newmd.replace("**", "")