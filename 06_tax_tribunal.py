# ---------------------------------------------------------------
# Tax Tribunal decisions (target=ttSpecialDecc) — search via XML,
# detail via JSON. A live example that the two steps of one target
# may speak different formats.
# ---------------------------------------------------------------
import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.law.go.kr/"}


def read_key():
    """Never hard-code the key. Read the env var first, then the local file."""
    oc = (os.environ.get("LAW_OC") or "").strip()
    if oc:
        return oc
    try:
        with open(r"C:\krlaw\law_oc.txt", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def http_get(url, params):
    full = url + "?" + urllib.parse.urlencode(params, encoding="utf-8")
    req = urllib.request.Request(full, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "replace")


# -- search (XML) ------------------------------------------------
def search_tribunal(keyword):
    """Search tribunal decisions -> human-readable list (str)."""
    raw = http_get("https://www.law.go.kr/DRF/lawSearch.do", {
        "OC": read_key(), "target": "ttSpecialDecc", "type": "XML",
        "query": keyword, "display": "10",
    })
    root = ET.fromstring(raw)
    items = []
    for child in list(root):
        if not list(child):
            continue
        d = {}
        for f in list(child):
            if f.text and f.text.strip():
                d[f.tag] = f.text.strip()
        if d:
            items.append(d)
    if not items:
        return "[검색결과 없음] '%s' — 키워드를 줄여 다시 검색하세요." % keyword

    lines = []
    for d in items:
        # Title/number field names vary by row — use whichever exists.
        title = d.get("사건명") or d.get("안건명") or d.get("재결례명") or "?"
        serial = ""
        for k, v in d.items():
            if k.endswith("일련번호"):       # *일련번호 = the ID key for the detail call
                serial = v
                break
        extra = " · ".join("%s %s" % (k, d[k])
                           for k in ("세목", "청구번호", "의결일자", "처분일자") if d.get(k))
        lines.append("[%s] %s%s" % (serial, title, ("\n   " + extra) if extra else ""))
    return "\n".join(lines)


# -- detail (JSON) -----------------------------------------------
def get_tribunal(serial):
    """Fetch one decision in full by its serial number (ID) -> display text."""
    raw = http_get("https://www.law.go.kr/DRF/lawService.do", {
        "OC": read_key(), "target": "ttSpecialDecc", "type": "JSON", "ID": str(serial),
    })
    data = json.loads(raw)
    # The top-level key name varies by target — grab the first dict value.
    node = next((v for v in data.values() if isinstance(v, dict)), None)
    if node is None:
        return "[본문 없음] 일련번호 %s — 응답에서 본문 노드를 찾지 못했습니다." % serial

    order = ("사건명", "청구번호", "세목", "의결일자", "처분일자",
             "주문", "재결요지", "이유")
    out = []
    shown = set()
    for k in order:                    # important fields first
        v = node.get(k)
        if isinstance(v, str) and v.strip():
            v = v.strip()
            out.append("%s:\n%s" % (k, v) if len(v) > 60 else "%s: %s" % (k, v))
            shown.add(k)
    for k, v in node.items():          # then any remaining string fields
        if k in shown or not isinstance(v, str) or not v.strip():
            continue
        v = v.strip()
        out.append("%s:\n%s" % (k, v) if len(v) > 60 else "%s: %s" % (k, v))
    return "\n\n".join(out) or "[본문 없음] 일련번호 %s" % serial


if __name__ == "__main__":
    # Hands-on demo (needs a key).
    print(search_tribunal("부당행위계산부인"))
