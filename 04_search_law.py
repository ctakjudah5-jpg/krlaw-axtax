# ---------------------------------------------------------------
# Statute search — raw results cause real accidents in two ways.
#
# 1) Matching is loose and ordering is alphabetical. Search "상법"
#    and the Commercial Act itself ranks about 34th (measured),
#    buried under compensation/indemnity acts. So: fetch one wide
#    page (display=100), pull exact-name matches to the top, and
#    show people only the head of the list.
#
# 2) Results mix in non-current ("연혁") versions. Quote one as
#    current law and you have an accident. So: warn on anything
#    whose 현행연혁코드 is not "현행".
# ---------------------------------------------------------------
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


def search_law(keyword):
    """Statute search -> human-readable list (str)."""
    raw = http_get("https://www.law.go.kr/DRF/lawSearch.do", {
        "OC": read_key(), "target": "law", "type": "XML",
        "query": keyword, "display": "100",   # wide, so the exact match lands inside the page
    })
    root = ET.fromstring(raw)
    items = []
    for child in list(root):              # a child with children = one result row
        if not list(child):
            continue
        d = {}
        for f in list(child):
            if f.text and f.text.strip():
                d[f.tag] = f.text.strip()
        if d:
            items.append(d)
    if not items:
        return ("[검색결과 없음] '%s' — 키워드를 줄여서 다시 검색하세요"
                "(공백은 AND 조건)." % keyword)

    # Fix for #1: exact-name matches go first.
    exact = [d for d in items if d.get("법령명한글", "") == keyword]
    rest = [d for d in items if d not in exact]
    ordered = exact + rest

    lines = []
    for d in ordered[:15]:                # show only the head of the list
        name = d.get("법령명한글", "?")
        mst = d.get("법령일련번호", "?")   # the key for detail lookups (lawService) = MST
        stat = d.get("현행연혁코드", "")
        ef = d.get("시행일자", "")
        # Fix for #2: warn on non-current versions.
        mark = "" if stat == "현행" else "  ⚠️ %s — 현행 아님(과거·예정 버전)" % (stat or "상태불명")
        lines.append("%s [MST %s] 시행 %s%s" % (name, mst, ef, mark))
    if len(ordered) > 15:
        lines.append("… 외 %d건 — 키워드를 더 좁혀 보세요." % (len(ordered) - 15))
    return "\n".join(lines)


if __name__ == "__main__":
    # Hands-on demo (needs a key).
    print(search_law("소득세법"))
    print()
    print(search_law("상법"))   # watch the exact match rise to the top
