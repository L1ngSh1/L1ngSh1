#!/usr/bin/env python3
"""Generate self-contained stack SVGs. Run from any directory; no dependencies."""
from pathlib import Path
from html import escape
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / 'assets/stack-icons'
# Product logos are vendored; research concepts use original neutral symbols.
GROUPS = [
 ('Languages', [('Python','python','#3776AB'),('C++','cplusplus','#58A6FF'),('Java','openjdk','#ED8B00'),('Bash','gnubash','#4EAA25'),('JavaScript','javascript','#F7DF1E')]),
 ('Analysis Infrastructure', [('Clang / LLVM','llvm','#F34B7D'),('CodeQL','query','#58A6FF'),('Clang AST','tree','#8B949E'),('Static Analysis','scan','#8B949E'),('Data Flow','flow','#8B949E'),('Taint Analysis','trace','#8B949E')]),
 ('Security Environment', [('Linux','linux','#FCC624'),('Kali Linux','kalilinux','#58A6FF'),('Docker','docker','#2496ED'),('Git','git','#F05032'),('Burp Suite','burpsuite','#FF6633'),('Metasploit','metasploit','#58A6FF'),('Frida','probe','#C9D1D9'),('mitmproxy','proxy','#8B949E'),('Nmap','scan','#8B949E')]),
 ('Agent & Evaluation Research', [('LLM Agents','agent','#3FB950'),('Prompt Injection','injection','#DA3633'),('Security Evaluation','shield','#8B949E'),('Reproducible Experiments','repeat','#8B949E')]),
]
FEATURED = ['Python','C++','Java','Docker','Kali Linux','Burp Suite','Metasploit','Git']
FEATURED_ART = {'Python':'python', 'C++':'cplusplus', 'Java':'java', 'Docker':'docker', 'Git':'git'}
SYMBOLS = {
 'query':'<path d="m7 5-4 7 4 7m10-14 4 7-4 7M14 4l-4 16"/>',
 'tree':'<path d="M12 5v5M5 18v-8h14v8"/><circle cx="12" cy="4" r="2"/><circle cx="5" cy="20" r="2"/><circle cx="19" cy="20" r="2"/>',
 'scan':'<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M3 12h18"/>',
 'flow':'<path d="M5 6h12m-4-3 4 3-4 3M19 18H7m4-3-4 3 4 3M5 6v12m14-12v12"/>',
 'trace':'<path d="M4 5h6v7h10M10 12v7h7"/><circle cx="4" cy="5" r="2"/><circle cx="20" cy="12" r="2"/><circle cx="17" cy="19" r="2"/>',
 'probe':'<path d="M3 12h5l3-7 3 14 3-7h4"/>',
 'proxy':'<path d="M3 7h18m-4-4 4 4-4 4M21 17H3m4-4-4 4 4 4M12 3v18"/>',
 'agent':'<rect x="4" y="7" width="16" height="14" rx="3"/><path d="M12 3v4M8 12v3m8-3v3m-8 3h8"/><circle cx="12" cy="2" r="1"/>',
 'injection':'<path d="M13 3h7v18h-7M2 12h13m-4-4 4 4-4 4"/>',
 'shield':'<path d="m12 2 8 3v6c0 5-4 9-8 11-4-2-8-6-8-11V5zM8 12l3 3 5-6"/>',
 'repeat':'<path d="M4 9a8 8 0 0 1 14-3l2 3M20 3v6h-6M20 15a8 8 0 0 1-14 3l-2-3M4 21v-6h6"/>',
}

def text(x,y,value,cls='item',extra=''):
 return f'<text x="{x}" y="{y}" class="{cls}" {extra}>{escape(value)}</text>'

def icon_defs():
 parts=[]
 for key in sorted({item[1] for _,items in GROUPS for item in items}):
  if key in SYMBOLS:
   body=f'<g fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{SYMBOLS[key]}</g>'
  else:
   root=ET.parse(ICONS/f'{key}.svg').getroot()
   body=''.join(f'<path fill="currentColor" d="{node.attrib["d"]}"/>' for node in root.iter() if node.tag.endswith('}path'))
   if not body: raise ValueError(f'No path in {key}')
  parts.append(f'<symbol id="icon-{key}" viewBox="0 0 24 24">{body}</symbol>')
 return '\n'.join(parts)

def use(key,x,y,size,color):
 return f'<use href="#icon-{key}" x="{x}" y="{y}" width="{size}" height="{size}" color="{color}" aria-hidden="true"/>'

def featured_defs():
 """Keep original-color artwork isolated from the monochrome inventory icons."""
 ET.register_namespace('', 'http://www.w3.org/2000/svg')
 parts=[]
 for key in FEATURED_ART.values():
  root=ET.parse(ICONS/'featured'/f'{key}.svg').getroot()
  ids={e.attrib['id']:f'featured-{key}-{e.attrib["id"]}' for e in root.iter() if 'id' in e.attrib}
  for element in root.iter():
   for attr,value in list(element.attrib.items()):
    if attr=='id':element.set(attr,ids[value])
    else:
     for old,new in ids.items():value=value.replace(f'url(#{old})',f'url(#{new})')
     element.set(attr,value)
  body=''.join(ET.tostring(e,encoding='unicode') for e in root)
  parts.append(f'<symbol id="icon-featured-{key}" viewBox="{root.attrib["viewBox"]}">{body}</symbol>')
 return '\n'.join(parts)

def generate(mobile=False):
 w,h=(720,1340) if mobile else (1200,700)
 font=22 if mobile else 18
 content=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
 '<title id="title">Security &amp; Engineering Stack</title>',
 '<desc id="desc">'+escape('; '.join(title+': '+', '.join(i[0] for i in items) for title,items in GROUPS))+'.</desc>',
 '<defs><style>.mono,.item,.meta{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,monospace}.heading{font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;font-weight:600;fill:#E6EDF3;font-size:'+str(26 if mobile else 23)+'px}.item{fill:#C9D1D9;font-size:'+str(font)+'px}.meta{fill:#8B949E;font-size:'+str(18 if mobile else 14)+'px;letter-spacing:1px}</style>',icon_defs(),featured_defs(),'</defs>',
 f'<rect width="{w}" height="{h}" rx="18" fill="#0D1117"/>',
 f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="17" fill="none" stroke="#30363D"/>',
 text(28,35,'RESEARCH TOOLCHAIN','meta'),text(w-28,35,'04 DOMAINS / 24 ENTRIES','meta','text-anchor="end"'),
 f'<path d="M1 56H{w-1}" stroke="#30363D"/>']
 lookup={i[0]:i for _,items in GROUPS for i in items}
 for i,name in enumerate(FEATURED):
  x,y=(76+(i%4)*152,80+(i//4)*112) if mobile else (116+i*128,82)
  label,key,color=lookup[name]
  art='featured-'+FEATURED_ART[name] if name in FEATURED_ART else key
  content.extend([f'<g data-featured="{escape(label,quote=True)}" role="img" aria-label="{escape(label,quote=True)}"><title>{escape(label)}</title>',use(art,x-4,y-4,80,color),'</g>'])
 positions=[(32,344,2,332),(32,552,2,332),(32,760,2,332),(32,1056,1,656)] if mobile else [(36,244,3,176),(636,244,2,258),(36,450,3,176),(636,450,1,528)]
 if not mobile:
  content.append('<path d="M600 222V630M36 410H1164" stroke="#21262D"/>')
 for index,((title,items),(x,y,cols,step)) in enumerate(zip(GROUPS,positions),1):
  if mobile: content.append(f'<path d="M32 {y-30}H688" stroke="#21262D"/>')
  content.extend([f'<path d="M{x} {y-8}h18" stroke="#DA3633" stroke-width="2"/>',text(x+30,y,title,'heading')])
  for i,(label,key,color) in enumerate(items):
   tx=x+(i%cols)*step;ty=y+52+(i//cols)*(44 if mobile else 42)
   content.extend([f'<g data-entry="{escape(label,quote=True)}">',use(key,tx,ty-20,24,color),text(tx+36,ty,label),'</g>'])
 fy=h-25
 content.extend([f'<path d="M28 {h-54}H{w-28}" stroke="#21262D"/>',f'<circle cx="34" cy="{fy-5}" r="3" fill="#3FB950"/>',text(46,fy,'SECURITY / ENGINEERING','meta'),text(w-28,fy,'BUILD · ANALYZE · VALIDATE','meta','text-anchor="end"'),'</svg>'])
 return '\n'.join(content)+'\n'

if __name__=='__main__':
 for mobile in (False,True):
  path=ROOT/'assets'/('stack-mobile.svg' if mobile else 'stack.svg')
  path.write_text(generate(mobile))
  print(f'Generated {path.name}')
