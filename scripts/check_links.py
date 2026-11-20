#!/usr/bin/env python3
"""Check local references in the published HTML and CSS against the Pages tree."""
import argparse
import json
import os
import posixpath
import re
from collections import Counter
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit

import tinycss2

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://funj-student.github.io/itasca-docs-cn/'
SITE_URL = urlsplit(SITE)
HTML_EXTENSIONS = ('.html', '.htm')
# The Sphinx theme emits its mobile stylesheet as a literal link tag.
WRITTEN_LINK = re.compile(r"""^[ \t]*document\.write\(\s*(['"])(<link\s[^<>\n]*>)\1\s*\)""", re.M)


def srcset_urls(value):
    # A URL may contain commas (notably data: images). A trailing comma or a
    # comma after the width/density descriptor separates candidates.
    value = value.strip()
    while value:
        value = value.lstrip(' ,\t\r\n\f')
        match = re.match(r'[^ \t\r\n\f]+', value)
        if not match:
            break
        url = match.group()
        value = value[match.end():]
        yield url.rstrip(',')
        if not url.endswith(','):
            _, _, value = value.partition(',')


def css_urls(tokens):
    """Walk CSS blocks and functions, including both forms of @import."""
    import_url = False
    for token in tokens:
        if token.type in ('comment', 'whitespace'):
            continue
        if token.type == 'url' or (import_url and token.type == 'string'):
            yield token.value, token.source_line
        elif token.type == 'function':
            if token.lower_name == 'url':
                for arg in token.arguments:
                    if arg.type == 'string':
                        yield arg.value, arg.source_line
            else:
                yield from css_urls(token.arguments)
        elif hasattr(token, 'content'):
            yield from css_urls(token.content)
        import_url = token.type == 'at-keyword' and token.lower_value == 'import'


@lru_cache(maxsize=512)
def parse_css(text):
    return tuple(css_urls(tinycss2.parse_component_value_list(text)))


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = set()
        self.references = []
        self.base_href = None
        self.raw_tag = None

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        self.raw_tag = tag if tag in ('style', 'script') else None
        for key, value in attrs:
            if not value:
                continue
            if key == 'id' or (tag == 'a' and key == 'name'):
                self.anchors.add(value)
            elif tag == 'base' and key == 'href':
                if self.base_href is None:
                    self.base_href = value
            elif key in ('href', 'xlink:href', 'src', 'poster', 'background') or (
                (tag, key) in (('object', 'data'), ('form', 'action'))
            ):
                self.references.append((value, line))
            elif key in ('srcset', 'imagesrcset'):
                self.references.extend((url, line) for url in srcset_urls(value))
            elif key == 'style':
                self.add_css(value, line)

    def handle_endtag(self, tag):
        if tag == self.raw_tag:
            self.raw_tag = None

    def add_css(self, text, line):
        self.references.extend((url, line + offset - 1) for url, offset in parse_css(text))

    def handle_data(self, data):
        if self.raw_tag == 'style':
            self.add_css(data, self.getpos()[0])
        elif self.raw_tag == 'script' and 'document.write' in data:
            for match in WRITTEN_LINK.finditer(data):
                link = Page()
                link.feed(match[2])
                line = self.getpos()[0] + data.count('\n', 0, match.start(2))
                self.references.extend((url, line) for url, _ in link.references)


def site_files(root):
    files = set()
    for directory, children, names in os.walk(root):
        children[:] = [d for d in children if d != '.git']
        parent = Path(directory).relative_to(root)
        files.update((parent / name).as_posix() for name in names)
    return files


def check_site(root, known_missing):
    files = site_files(root)
    anchors = {}
    fragments = []
    errors = Counter()
    remaining = known_missing.copy()

    def report(kind, source, line, raw):
        errors[kind] += 1
        print(f'{source}:{line}: {kind}: {raw}')

    for source in sorted(files):
        extension = Path(source).suffix.lower()
        if extension not in (*HTML_EXTENSIONS, '.css'):
            continue
        text = (root / source).read_text(encoding='utf-8-sig')
        base = SITE + quote(source)
        if extension == '.css':
            # A fragment-only CSS paint/filter URL refers to the styled document.
            references = ((url, line) for url, line in parse_css(text) if not url.startswith('#'))
        else:
            page = Page()
            page.feed(text)
            page.close()
            anchors[source] = page.anchors
            references = page.references
            if page.base_href is not None:
                base = urljoin(base, page.base_href)

        for raw, line in references:
            url = urlsplit(urljoin(base, raw.strip()))
            if url.scheme == 'file':
                report('missing file', source, line, raw)
                continue
            if url.scheme not in ('http', 'https') or url.netloc.lower() != SITE_URL.netloc:
                continue
            path = unquote(url.path)
            target = posixpath.normpath(path)
            if target == SITE_URL.path.rstrip('/'):
                target += '/'
            if not target.startswith(SITE_URL.path):
                # A fully qualified link to another site on the same Pages host.
                if urlsplit(raw).netloc:
                    continue
                report('missing file', source, line, raw)
                continue
            target = target.removeprefix(SITE_URL.path)
            if path.endswith('/') or target not in files:
                target = posixpath.join(target, 'index.html')
            if target not in files:
                key = (source, raw)
                if remaining[key]:
                    remaining[key] -= 1
                    print(f'{source}:{line}: known missing file: {raw}')
                else:
                    report('missing file', source, line, raw)
                continue
            fragment = unquote(url.fragment).split(':~:', 1)[0]
            if fragment and target.lower().endswith(HTML_EXTENSIONS):
                fragments.append((source, line, raw, target, fragment))

    # Forward references can now be checked without reading any page twice.
    for source, line, raw, target, fragment in fragments:
        if fragment not in anchors[target] and fragment.lower() != 'top':
            report('missing anchor', source, line, raw)
    for (source, raw), count in remaining.items():
        if count:
            report('stale known-missing entry', source, '-', raw)
    known = known_missing.total() - remaining.total()
    print(f"pages={len(anchors)} missing_files={errors['missing file'] + known} "
          f"missing_anchors={errors['missing anchor']} known_missing_files={known}")
    if not anchors:
        print(f'No HTML pages found in {root}')
        return 1
    return int(bool(errors))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, nargs='?', default=ROOT)
    parser.add_argument('--known-missing', type=Path, help='JSON list of exact (page, URL) exceptions')
    args = parser.parse_args()
    entries = json.loads(args.known_missing.read_text(encoding='utf-8')) if args.known_missing else []
    raise SystemExit(check_site(args.root.resolve(), Counter((e['page'], e['url']) for e in entries)))
