"""Archive public PortalEdu posts and their images. Python standard library only."""
import concurrent.futures
import gzip
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://portal.edu.gva.es/blogs/s1/angelfilo/'
STORE = ROOT / 'source/inventario.json'
UA = 'FilosofemasArchive/1.0 (+https://amartinsanto.github.io/)'

def fetch(url):
    if urllib.parse.urlsplit(url).scheme not in ('https', 'http'):
        raise ValueError('Unsupported URL scheme')
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(request, timeout=25) as response:
                raw = response.read()
            return gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw
        except (OSError, urllib.error.URLError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)

class Capture(HTMLParser):
    def __init__(self, css_class):
        super().__init__(convert_charrefs=False)
        self.css_class = css_class
        self.depth = 0
        self.tag = None
        self.done = False
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if not self.depth:
            if self.css_class in dict(attrs).get('class', '').split():
                self.depth, self.tag = 1, tag
            return
        if tag == self.tag:
            self.depth += 1
        self.parts.append(self.get_starttag_text())
    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == self.tag:
            self.depth -= 1
        if self.depth:
            self.parts.append('</' + tag + '>')
        else:
            self.done = True
    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)
    def handle_entityref(self, data):
        self.handle_data('&' + data + ';')
    def handle_charref(self, data):
        self.handle_data('&#' + data + ';')

def capture(document, css_class):
    parser = Capture(css_class)
    parser.feed(document)
    return ''.join(parser.parts)

def plain(text):
    return html.unescape(re.sub('<[^>]*>', '', text)).strip()

def links(document, origin):
    return [urllib.parse.urljoin(origin, html.unescape(x))
            for x in re.findall(r'href=[\'\"]([^\'\"]+)', document, re.I)]

def discover():
    todo, seen, posts = [BASE], set(), set()
    while todo:
        url = todo.pop(0)
        if url in seen:
            continue
        seen.add(url)
        if len(seen) > 200:
            raise RuntimeError('Unexpected pagination; refusing a partial archive')
        document = fetch(url).decode('utf-8')
        if '<title' not in document:
            raise ValueError('Unexpected listing response: ' + url)
        # Only named post cards and the existing archive entries, never API/login URLs.
        card_links = []
        for match in re.finditer(r'<(?:h[1-6])\b[^>]*>.*?</h[1-6]>', document, re.S | re.I):
            card_links.extend(links(match.group(), url))
        for target in card_links:
            if not target.startswith(BASE):
                continue
            relative = target[len(BASE):].strip('/')
            if re.fullmatch(r'[a-zA-Z0-9_%-]+', relative) and not relative.startswith('wp-') and relative not in ('feed','comments'):
                posts.add(BASE + relative + '/')
        for target in links(document, url):
            if re.fullmatch(re.escape(BASE) + r'page/\d+/?', target):
                target = target.rstrip('/') + '/'
                if target not in seen and target not in todo:
                    todo.append(target)
    if not posts:
        raise RuntimeError('No posts detected. Keeping the previous archive intact.')
    print(f'Listings: {len(seen)}; public posts: {len(posts)}', flush=True)
    return sorted(posts)

def parse_post(url, document):
    content = capture(document, 'contenido-post') or capture(document, 'entry-content')
    title_match = re.search(r'<h1\b[^>]*>(.*?)</h1>', document, re.S | re.I)
    date = plain(capture(document, 'fecha'))
    if not content or not title_match or not date:
        raise RuntimeError('Incomplete post; no changes will be published: ' + url)
    content = re.split(r'<div class="addtoany_share', content)[0]
    slug = urllib.parse.urlsplit(url).path.rstrip('/').split('/')[-1]
    if not re.fullmatch(r'[a-zA-Z0-9_%-]+', slug):
        raise ValueError('Invalid post slug')
    return {'url': url, 'slug': slug, 'title': plain(title_match.group(1)),
            'date': date, 'category': plain(capture(document, 'categoria')) or 'Filosofía',
            'html': content, 'featured': capture(document, 'imagen-destacada')}

def retrieve_post(url):
    post = parse_post(url, fetch(url).decode('utf-8'))
    print('Retrieved: ' + post['title'], flush=True)
    return post

def merge_posts(archived, fresh):
    # Absence from the public blog never deletes an archived entry.
    merged = {p['url']: p for p in archived}
    merged.update({p['url']: p for p in fresh})
    return sorted(merged.values(), key=lambda p: p['url'])

def image_urls(posts):
    urls = set()
    for post in posts:
        for source in re.findall(r'<img[^>]+src=[\'\"]([^\'\"]+)', post['html'] + post['featured'], re.I):
            target = urllib.parse.urljoin(post['url'], html.unescape(source))
            if urllib.parse.urlsplit(target).scheme in ('http', 'https'):
                urls.add(target)
    return sorted(urls)

def save_if_changed(path, content):
    if path.exists() and path.read_bytes() == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return True

def download_image(url, known):
    suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
    if suffix not in ('.jpg','.jpeg','.png','.gif','.webp','.svg','.avif','.ico','.bmp'):
        suffix = '.img'
    name = known.get(url) or hashlib.sha256(url.encode()).hexdigest()[:16] + suffix
    if Path(name).name != name:
        raise ValueError('Invalid asset filename')
    target = ROOT / 'imagenes' / name
    try:
        content = fetch(url)
        if not content or content.lstrip().lower().startswith((b'<!doctype html', b'<html')):
            raise ValueError('Invalid image response')
        changed = save_if_changed(target, content)
        return url, name, changed
    except Exception:
        if url in known and target.is_file():
            print('Retaining previously downloaded image: ' + url, flush=True)
            return url, name, False
        raise

def main():
    previous = json.loads(STORE.read_text(encoding='utf-8'))
    urls = discover()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        fresh = list(pool.map(retrieve_post, urls))
    merged = merge_posts(previous['posts'], fresh)
    known = previous.get('images', {})
    assets = dict(known)
    changed_images = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda u: download_image(u, known), image_urls(fresh)))
    for url, name, changed in results:
        assets[url] = name
        changed_images += int(changed)
    result = {'source': BASE, 'posts': merged, 'images': assets}
    serialized = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()
    changed = save_if_changed(STORE, serialized)
    print(f'Archive: {len(merged)} posts; updated images: {changed_images}; data changed: {changed}', flush=True)

if __name__ == '__main__':
    main()
