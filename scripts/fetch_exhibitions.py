import json
from datetime import date
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/exhibitions.json"
TIMEOUT=30
HEADERS={"User-Agent":"Mozilla/5.0 Korean-National-Museum-Monitor/1.0"}
MUSEUMS=[
("central","국립중앙박물관","https://vcm.museum.go.kr/MUSEUM/contents/M0202010000.do?menuId=current"),
("gyeongju","국립경주박물관","https://gyeongju.museum.go.kr/kor/html/sub02/0202.html"),
("gwangju","국립광주박물관","https://gwangju.museum.go.kr/kor/html/sub02/0202.html"),
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
def fetch(url):
    r=requests.get(url,headers=HEADERS,timeout=TIMEOUT)
    r.raise_for_status()
    return BeautifulSoup(r.text,"lxml")
def run():
    payload=json.loads(OUT.read_text(encoding="utf-8"))
    payload.setdefault("meta",{})["lastChecked"]=date.today().isoformat()
    failures=[]
    for mid,name,url in MUSEUMS:
        try:
            soup=fetch(url)
            if not soup.get_text(" ",strip=True): raise RuntimeError("empty official page")
        except Exception as e:
            failures.append({"museum_id":mid,"museum":name,"error":str(e)})
    payload["meta"]["sourceHealth"]=failures
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": run()
