# ---------------------------------------------------------------
# First reading — the "search -> detail" two-step chain, shown
# with statutory interpretations (target=expc).
#
# Everything built in this course rests on four ideas in this file:
#   1) search (lawSearch.do) returns only a list  — light, many items
#   2) detail (lawService.do) returns one item in full — heavy, one item
#   3) the key linking the two steps = 법령해석례일련번호 (serial number)
#   4) a tool always returns one fixed shape, success or failure:
#      {"content": [{"type": "text", "text": ...}], "isError": ...}
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
    """GET url with params -> response body (str)."""
    full = url + "?" + urllib.parse.urlencode(params, encoding="utf-8")
    req = urllib.request.Request(full, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "replace")


# -- step 1: search (XML) ----------------------------------------
def search_expc(keyword):
    """Search interpretations — returns the list only."""
    raw = http_get("https://www.law.go.kr/DRF/lawSearch.do", {
        "OC": read_key(), "target": "expc", "type": "XML",
        "query": keyword, "display": "10",
    })
    root = ET.fromstring(raw)
    items = []
    # Search-XML rule: a child that has children = one result row,
    #                  a leaf child = metadata (totalCnt, page, ...)
    for child in list(root):
        if not list(child):
            continue
        d = {}
        for f in list(child):
            if f.text and f.text.strip():
                d[f.tag] = f.text.strip()
        if d:
            items.append(d)
    return items
    # NOTE: "...상세링크" (detail-link) fields may embed your OC key.
    #       Never include link fields in anything you print or return.


# -- step 2: detail (JSON) ---------------------------------------
def get_expc(serial):
    """Fetch the full text by the serial number (ID) from search results."""
    raw = http_get("https://www.law.go.kr/DRF/lawService.do", {
        "OC": read_key(), "target": "expc", "type": "JSON", "ID": str(serial),
    })
    data = json.loads(raw)
    node = data.get("ExpcService")
    if not isinstance(node, dict):
        return None          # unknown serial — let the caller notice
    return {
        "안건명": node.get("안건명", ""),
        "해석일자": node.get("해석일자", ""),
        "해석기관": node.get("해석기관명", ""),
        "질의요지": node.get("질의요지", ""),
        "회답": node.get("회답", ""),
    }


# -- the one fixed shape every MCP tool returns ------------------
def tool_result(text, is_error=False):
    """Same shape for success and failure; only isError flips.
    Claude trusts this shape — return anything else and the tool breaks."""
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


if __name__ == "__main__":
    # Hands-on demo: search, then fetch the first hit in full (needs a key).
    found = search_expc("주차장")
    for it in found[:3]:
        print(it.get("법령해석례일련번호"), "|", it.get("안건명"), "|", it.get("회신일자"))
    if found:
        body = get_expc(found[0]["법령해석례일련번호"])
        if body:
            print("\n===", body["안건명"], "(", body["해석일자"], ")")
            print((body["회답"] or "")[:300])
