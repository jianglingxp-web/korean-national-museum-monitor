import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/exhibitions.json"
TIMEOUT=30
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; Korean-National-Museum-Monitor/1.0)"}

MUSEUMS=[
("central","국립중앙박물관","https://vcm.museum.go.kr/MUSEUM/contents/M0202010000.do?menuId=current"),
("gyeongju","국립경주박물관","https://gyeongju.museum.go.kr/kor/html/sub02/0202.html"),
("gwangju","국립광주博物館","https://gwangju.museum.go.kr/kor/html/sub02/0202.html"),
("jeonju","국립전주박물관","https://jeonju.museum.go.kr/kor/html/sub02/0202.html"),
("daegu","국립대구박물관","https://daegu.museum.go.kr/kor/html/sub02/0202.html"),
("buyeo","국립부여박물관","https://buyeo.museum.go.kr/kor/html/sub02/0202.html"),
("gongju","국립공주박물관","https://gongju.museum.go.kr/kor/html/sub02/0202.html"),
("jinju","국립진주박물관","https://jinju.museum.go.kr/kor/html/sub02/0202.html"),
("cheongju","국립청주박물관","https://cheongju.museum.go.kr/kor/html/sub02/0202.html"),
("gimhae","국립김해박물관","https://gimhae.museum.go.kr/kr/html/sub02/020201.html"),
("jeju","국립제주박물관","https://jeju.museum.go.kr/kor/html/sub02/0202.html"),
("chuncheon","국립춘천박물관","https://chuncheon.museum.go.kr/kor/html/sub02/0202.html"),
("naju","국립나주박물관","https://naju.museum.go.kr/prog/spclexht/A/kor/sub02_02_01/list.do"),
("iksan","국립익산박물관","https://iksan.museum.go.kr/kor/html/sub02/0202.html"),
]

RANGE_RE=re.compile(r"(20\d{2})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})\s*[~–-]\s*(?:(20\d{2})[.\-/]\s*)?(\d{1,2})[.\-/]\s*(\d{1,2})")
TYPE_WORDS=("특별전","기획전","특별기획전","국제교류전","테마전","상설전")

def fetch(url):
    r=requests.get(url,headers=HEADERS,timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text,"lxml"),r.url

def norm_date(y,m,d):
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

def extract_range(text):
    text=re.sub(r"\s+"," ",text)
    m=RANGE_RE.search(text)
    if not m: return None
    y1,m1,d1,y2,m2,d2=m.groups()
    return norm_date(y1,m1,d1),norm_date(y2 or y1,m2,d2)

def clean_title(text):
    return re.sub(r"\s+"," ",text).strip(" -|·")[:180]

def discover(soup,base_url,mid,museum_zh):
    found=[]; seen=set()
    for a in soup.find_all("a",href=True):
        title=clean_title(a.get_text(" ",strip=True))
        if len(title)<2 or title in {"자세히보기","상세보기","더보기","View"}: continue
        node=a; rng=None; context=title
        for _ in range(5):
            node=node.parent if node else None
            if not node: break
            context=clean_title(node.get_text(" ",strip=True))
            rng=extract_range(context)
            if rng: break
        if not rng: continue
        href=urljoin(base_url,a["href"])
        key=(title,rng[0],rng[1])
        if key in seen: continue
        seen.add(key)
        typ=next((w for w in TYPE_WORDS if w in context),"")
        found.append({"museum_id":mid,"museum_zh":museum_zh,"title_ko":title,"start":rng[0],"end":rng[1],"type":typ,"source_url":href})
    return found

def merge(payload,items,checked):
    existing={(x.get("museum_id"),x.get("title_ko"),x.get("start")):x for x in payload.get("exhibitions",[])}
    for item in items:
        key=(item["museum_id"],item["title_ko"],item["start"])
        old=existing.get(key)
        if old:
            changed=any(old.get(k)!=item.get(k) for k in ("end","type","source_url"))
            old.update({k:v for k,v in item.items() if v})
            old["lastChecked"]=checked
            if changed: old["isUpdated"]=True
        else:
            slug=re.sub(r"[^a-z0-9]+","-",item["title_ko"].lower()).strip("-")[:70]
            item["id"]=item["museum_id"]+"-"+slug+"-"+item["start"]
            item.update({"title_zh":"","important":item.get("type") in ("특별전","특별기획전"),"discovery":"auto","lastChecked":checked,"isNew":True,"isUpdated":False})
            payload.setdefault("exhibitions",[]).append(item)

def run():
    payload=json.loads(OUT.read_text(encoding="utf-8"))
    checked=date.today().isoformat()
    payload.setdefault("meta",{}).update({"lastChecked":checked,"sourcePolicy":"official-museum-sites"})
    failures=[]; count=0
    for mid,name,url in MUSEUMS:
        try:
            soup,final=fetch(url)
            if not soup.get_text(" ",strip=True): raise RuntimeError("empty official page")
            items=discover(soup,final,mid,name)
            count+=len(items)
            merge(payload,items,checked)
        except Exception as e:
            failures.append({"museum_id":mid,"museum":name,"error":str(e)})
    payload["meta"]["sourceHealth"]=failures
    payload["meta"]["lastDiscoveryCount"]=count
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")

if __name__=="__main__":
    run()
