# ---------------------------------------------------------------
# Korea Ministry of Government Legislation (law.go.kr) OPEN API.
# These two endpoints are all you need. Every lookup is a
# two-step walk: search (list) -> detail (full text).
# ---------------------------------------------------------------

BASE = "https://www.law.go.kr/DRF"

SEARCH_URL = BASE + "/lawSearch.do"    # search: returns a light list of hits
DETAIL_URL = BASE + "/lawService.do"   # detail: returns one item in full (heavy)

# Common query parameters
#   OC     = your personal API key (issued at open.law.go.kr)
#   target = what to look up: law | expc (interpretations) | ttSpecialDecc (tax tribunal) ...
#   type   = response format. In this course: search=XML, detail=JSON.

# Required request headers. Without Referer the API answers
# "user verification failed" even when the OC key is valid.
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.law.go.kr/",
}

# Note: spaces in a query act as AND. One or two keywords beat long sentences.
