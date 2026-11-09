import json, re, html, shutil, zipfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'source'
OUT = ROOT / '_site'
DATA = json.loads((SRC / 'inventario.json').read_text())
POSTS = DATA['posts']
MONTHS = {m: i + 1 for i, m in enumerate('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split())}
def datekey(p):
    d, m, y = p['date'].split(' de ')
    return f'{y}-{MONTHS[m]:02d}-{int(d):02d}'
POSTS.sort(key=datekey, reverse=True)
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(exist_ok=True)
(OUT / 'entradas').mkdir(exist_ok=True)
shutil.copytree(ROOT / 'imagenes', OUT / 'imagenes', dirs_exist_ok=True)
esc = html.escape

CSS = '''
@import url("https://fonts.googleapis.com/css2?family=Cormorant+SC:wght@500&display=swap");
:root{--paper:#f7f4ed;--ink:#252d2a;--muted:#636c65;--accent:#346451;--line:#d8dbcf;--serif:Georgia,'Times New Roman',serif;--sans:system-ui,-apple-system,Segoe UI,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.65 var(--sans)}a{color:var(--accent);text-underline-offset:4px}a:hover{color:#182f25}button,input,select{font:inherit}a:focus-visible,input:focus-visible,select:focus-visible,button:focus-visible{outline:3px solid #b27734;outline-offset:5px}.skip{position:absolute;top:-90px;left:20px;z-index:20;background:white;padding:12px}.skip:focus{top:10px}.shell{max-width:1160px;margin:auto;padding:0 32px}.masthead{border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:20px;padding:26px 0}.brand{font:bold 29px var(--serif);color:var(--ink);text-decoration:none;letter-spacing:-1px}.masthead nav{display:flex;gap:25px;font-size:14px}.masthead nav a{color:var(--ink);text-decoration:none}.kicker{font:12px/1.4 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}.intro{padding:70px 0 50px;max-width:830px}.intro h1{font:normal clamp(40px,6vw,72px)/1.07 var(--serif);letter-spacing:-2px;margin:22px 0}.intro p{max-width:640px;color:var(--muted);font-size:18px}.author{font-size:14px;letter-spacing:.02em}.feature{display:grid;grid-template-columns:1fr 1fr;gap:45px;align-items:center;padding:30px 0 50px;border-bottom:1px solid var(--line)}.feature .cover{height:350px;width:100%;object-fit:cover;border-radius:3px}.feature h2{font:normal clamp(30px,3.5vw,45px)/1.12 var(--serif);letter-spacing:-1px;margin:17px 0}.feature h2 a,.card h3 a{text-decoration:none;color:var(--ink)}.excerpt{color:var(--muted);font-size:16px}.read{display:inline-block;font-size:14px;margin-top:10px}.meta{font-size:13px;color:var(--muted)}.archive-head{margin-top:55px;display:flex;justify-content:space-between;align-items:baseline;gap:20px}.archive-head h2{font:normal 36px var(--serif);margin:0}.filters{display:flex;gap:15px;margin:25px 0 10px}.filters input,.filters select{border:1px solid var(--line);background:#fffdf8;border-radius:3px;padding:12px 14px;max-width:100%;color:var(--ink)}.filters input{width:100%}.filters label:first-child{flex:1}.filters label span{display:block;font-size:12px;margin-bottom:7px;color:var(--muted)}#count{font-size:13px;color:var(--muted);min-height:25px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 30px;margin-top:12px}.card{border-top:1px solid var(--line);padding:28px 0 35px;min-width:0}.card img{width:100%;height:185px;object-fit:cover;border-radius:2px;margin-bottom:15px}.card h3{font:normal 26px/1.2 var(--serif);letter-spacing:-.4px;margin:12px 0}.card .excerpt{font-size:14px}.card[hidden],.feature[hidden]{display:none}footer{border-top:1px solid var(--line);margin-top:55px;padding:28px 0 40px;color:var(--muted);font-size:13px;display:flex;justify-content:space-between;gap:20px}footer a{color:inherit}.article{max-width:760px;margin:65px auto}.article h1{font:normal clamp(34px,5vw,55px)/1.12 var(--serif);letter-spacing:-1px;margin:20px 0}.article .prose{font:20px/1.85 var(--serif);margin-top:40px;overflow-wrap:anywhere}.prose p{margin:1.2em 0}.prose img{max-width:100%;height:auto}.prose figure{margin:30px 0}.prose figcaption{font:13px/1.5 var(--sans);color:var(--muted);margin-top:8px}.prose h2,.prose h3{line-height:1.25}.prose blockquote{margin:25px 0;padding-left:24px;border-left:3px solid var(--accent)}.prose pre{white-space:pre-wrap}.prose table{max-width:100%;font-size:16px;border-collapse:collapse}.prose td,.prose th{padding:8px;border:1px solid var(--line)}.source{border-top:1px solid var(--line);padding-top:20px;margin-top:45px;font-size:13px;color:var(--muted)}.postnav{display:grid;grid-template-columns:1fr 1fr;gap:25px;margin-top:35px}.postnav a{font-size:14px}.postnav span{display:block;color:var(--muted);font-size:12px}.postnav .next{text-align:right}.article-hero{max-width:100%;height:auto;margin-top:30px}.empty{padding:30px 0}.video-link{border:1px solid var(--line);padding:15px;font:15px var(--sans)}
@media(max-width:800px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.feature{gap:25px}.feature .cover{height:280px}.shell{padding:0 22px}.intro{padding-top:45px}}
@media(max-width:540px){.masthead{align-items:flex-start;flex-direction:column;gap:12px}.masthead nav{gap:20px}.intro h1{letter-spacing:-1px}.intro{padding:35px 0 20px}.feature{grid-template-columns:1fr;gap:15px}.feature .cover{height:245px}.grid{grid-template-columns:1fr}.card{display:grid;grid-template-columns:1fr;gap:0}.card img{height:220px}.filters{flex-direction:column}.filters select{width:100%}.article{margin:40px auto}.article .prose{font-size:19px}.archive-head{align-items:flex-start;flex-direction:column;gap:0}footer{flex-direction:column}.postnav{grid-template-columns:1fr}.postnav .next{text-align:left}}
.filters[hidden]{display:none}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}

.intro h1{font-family:"Cormorant SC",Georgia,serif;font-weight:500;letter-spacing:.015em;line-height:1.12}
'''
(OUT / 'style.css').write_text(CSS)

def header(prefix):
    return f'<a class="skip" href="#contenido">Saltar al contenido</a><div class="shell"><header class="masthead"><a class="brand" href="{prefix}index.html">Filosofemas<span aria-hidden="true">.</span></a><nav aria-label="Principal"><a href="{prefix}index.html">Inicio</a><a href="{prefix}index.html#archivo">Archivo</a><a href="{prefix}entradas/presentacion.html">Presentación</a></nav></header>'
def footer():
    return '<footer><span>Ángel Martín Santo · Filosofemas</span><a href="https://portal.edu.gva.es/blogs/s1/angelfilo/">El blog en PortalEdu ↗</a></footer></div>'
def document(title, body, prefix='', description='Filosofía, literatura y educación. Un blog de Ángel Martín Santo.', slug=''):
    canonical = 'https://amartinsanto.github.io/' + slug
    return f'<!doctype html>\n<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} · Filosofemas</title><meta name="description" content="{esc(description, quote=True)}"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="{prefix}style.css"><meta name="theme-color" content="#f7f4ed"></head><body>{header(prefix)}{body}{footer()}</body></html>'
def plaintext(s):
    return ' '.join(html.unescape(re.sub('<[^>]*>', ' ', s)).split())
def excerpt(p, n=185):
    text = plaintext(p['html'])
    return text if len(text) <= n else text[:n].rsplit(' ',1)[0] + '…'
def image(p):
    s = p['featured'] or p['html']
    m = re.search(r'<img[^>]+src=[\'\"]([^\'\"]+)', s)
    return DATA['images'].get(html.unescape(m.group(1))) if m else None
def thumbnail(p, cls=''):
    name = image(p)
    return f'<img class="{cls}" src="imagenes/{name}" alt="" loading="lazy" width="600" height="360">' if name else ''

class Sanitize(HTMLParser):
    def __init__(self, url):
        super().__init__(convert_charrefs=False); self.url=url;self.out=[];self.skip=0
    def handle_starttag(self,t,a):
        d=dict(a)
        if t in ['script','iframe','form']:
            if t=='iframe' and not self.skip:
                u=urljoin(self.url,d.get('src',''))
                self.out.append('<p class="video-link"><a href="'+esc(u,quote=True)+'">Ver vídeo en su plataforma original ↗</a></p>')
            self.skip+=1;return
        if self.skip:return
        attrs=[]
        for k,v in a:
            if k in ['srcset','sizes','loading','fetchpriority'] or k.startswith('on'):continue
            if k in ['href','src','poster'] and v:
                absolute=urljoin(self.url,v)
                if absolute.startswith('javascript:'):continue
                if absolute in DATA['images']:v='../imagenes/'+DATA['images'][absolute]
                elif absolute.rstrip('/')+'/' in LINKS:v=LINKS[absolute.rstrip('/')+'/']
                else:v=absolute
            attrs.append(k if v is None else k+'="'+esc(v,quote=True)+'"')
        self.out.append('<'+t+(' '+' '.join(attrs) if attrs else '')+'>')
    def handle_startendtag(self,t,a):self.handle_starttag(t,a)
    def handle_endtag(self,t):
        if t in ['script','iframe','form']:
            self.skip=max(0,self.skip-1);return
        if not self.skip:self.out.append('</'+t+'>')
    def handle_data(self,s):
        if not self.skip:self.out.append(s)
    def handle_entityref(self,s):self.handle_data('&'+s+';')
    def handle_charref(self,s):self.handle_data('&#'+s+';')
LINKS={p['url']:p['slug']+'.html' for p in POSTS}
for i,p in enumerate(POSTS):
    sanitizer=Sanitize(p['url']);sanitizer.feed(p['html']);content=''.join(sanitizer.out)
    hero=''
    if '<img' not in content and image(p):hero=f'<img class="article-hero" src="../imagenes/{image(p)}" alt="">'
    reading=max(1,round(len(plaintext(p['html']).split())/220))
    body=f'<main id="contenido" class="article"><a class="kicker" href="../index.html#archivo">{esc(p["category"])}</a><h1>{esc(p["title"])}</h1><p class="meta"><time datetime="{datekey(p)}">{esc(p["date"])}</time> · Ángel Martín Santo · {reading} min de lectura</p>{hero}<div class="prose">{content}</div><p class="source">Publicado originalmente en <a href="{esc(p["url"])}">PortalEdu</a>. Texto e imágenes conservados de la publicación original.</p><nav class="postnav" aria-label="Otras entradas">'
    if i+1<len(POSTS):
        prev=POSTS[i+1];body+=f'<a href="{prev["slug"]}.html"><span>← Anterior</span>{esc(prev["title"])}</a>'
    else:body+='<div></div>'
    if i>0:
        nxt=POSTS[i-1];body+=f'<a class="next" href="{nxt["slug"]}.html"><span>Siguiente →</span>{esc(nxt["title"])}</a>'
    body+='</nav></main>'
    (OUT/'entradas'/(p['slug']+'.html')).write_text(document(p['title'],body,'../',excerpt(p),'entradas/'+p['slug']+'.html'))

latest=POSTS[0]
body='<main id="contenido"><section class="intro"><div class="kicker">El cuaderno de Ángel Martín Santo</div><h1>Filosofía, educación y afinidades electivas</h1><p>Sin propósito, utilidad ni público.</p></section>'
body+=f'<section class="feature" aria-labelledby="ultima">{thumbnail(latest,"cover")}<div><div class="kicker">Última entrada · {esc(latest["category"])}</div><h2 id="ultima"><a href="entradas/{latest["slug"]}.html">{esc(latest["title"])}</a></h2><p class="meta">{esc(latest["date"])}</p><p class="excerpt">{esc(excerpt(latest,240))}</p><a class="read" href="entradas/{latest["slug"]}.html">Leer la entrada →</a></div></section>'
body+=f'<section id="archivo" aria-labelledby="titulo-archivo"><div class="archive-head"><h2 id="titulo-archivo">Archivo de entradas</h2><p class="meta">{len(POSTS)} textos · {min(datekey(p)[:4] for p in POSTS)}–{max(datekey(p)[:4] for p in POSTS)}</p></div><div class="filters" id="filters" hidden><label><span>Buscar en títulos y textos</span><input id="search" type="search" placeholder="Un autor, una idea, una lectura…" autocomplete="off"></label><label><span>Filtrar por tema</span><select id="category"><option value="">Todos los temas</option>'
for c in sorted({p['category'] for p in POSTS}):body+=f'<option>{esc(c)}</option>'
body+=f'</select></label></div><p id="count" role="status" aria-live="polite">{len(POSTS)} entradas</p><div class="grid" id="posts">'
for p in POSTS:
    body+=f'<article class="card" data-slug="{p["slug"]}" data-category="{esc(p["category"],quote=True)}">{thumbnail(p)}<div class="kicker">{esc(p["category"])}</div><h3><a href="entradas/{p["slug"]}.html">{esc(p["title"])}</a></h3><p class="meta">{esc(p["date"])}</p><p class="excerpt">{esc(excerpt(p))}</p></article>'
body+='</div><p class="empty" id="empty" hidden>No hay entradas que coincidan. Prueba con otra palabra o tema.</p></section></main>'
# Embedded data lets the search work from disk as well as GitHub Pages.
searchdata={p['slug']:plaintext(p['title']+' '+p['html']) for p in POSTS}
body+='<script type="application/json" id="search-data">'+json.dumps(searchdata,ensure_ascii=False).replace('<','\\u003c')+'</script><script src="search.js" defer></script>'
(OUT/'index.html').write_text(document('Filosofía, literatura y educación',body))
(OUT/'search.js').write_text('''
const normalize=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLocaleLowerCase('es');
const source=JSON.parse(document.getElementById('search-data').textContent);
const texts=Object.fromEntries(Object.entries(source).map(([k,v])=>[k,normalize(v)]));
const cards=[...document.querySelectorAll('.card')];
const input=document.getElementById('search'),category=document.getElementById('category');
document.getElementById('filters').hidden=false;
function filter(){const words=normalize(input.value).trim().split(/\\s+/).filter(Boolean);let count=0;for(const card of cards){const show=(!category.value||card.dataset.category===category.value)&&words.every(w=>texts[card.dataset.slug].includes(w));card.hidden=!show;if(show)count++;}document.getElementById('count').textContent=count+' '+(count===1?'entrada':'entradas');document.getElementById('empty').hidden=count!==0;}
input.addEventListener('input',filter);category.addEventListener('change',filter);
''')
(OUT/'.nojekyll').write_text('')

# Do not publish if a required image or local page is missing.
class ValidateLinks(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ('href', 'src') or not value or value.startswith(('http:', 'https:', 'data:', 'mailto:', '#')):
                continue
            target = self.file.parent / value.split('#')[0]
            if not target.exists():
                raise RuntimeError(f'Missing local resource in {self.file.name}: {value}')

for page in OUT.rglob('*.html'):
    validator = ValidateLinks()
    validator.file = page
    validator.feed(page.read_text(encoding='utf-8'))
print(f'Generated and checked {len(POSTS)} posts in {OUT}')
