# ---------------------------------------------------------------
# MCP server skeleton — this alone plugs into the Claude desktop app.
#
# The #1 trap: stdout is the JSON-RPC channel to Claude.
# One stray print() poisons the channel and the connection dies.
# Anything meant for humans (logs) must go to stderr.
# ---------------------------------------------------------------
import json
import sys

# Required on Korean Windows: force UTF-8, or Hangul breaks and the link drops.
sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8", newline="\n")
sys.stderr.reconfigure(encoding="utf-8")


def log(*args):
    """Logs always go to stderr. (stdout carries protocol data only.)"""
    print(*args, file=sys.stderr, flush=True)


# -- the tools this server exposes -------------------------------
TOOLS = [
    {
        "name": "ping",
        "description": "서버가 살아 있는지 확인한다. 부르면 pong 을 돌려준다.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def call_tool(name, args):
    """Run one tool. Same shape for success and failure; only isError differs."""
    if name == "ping":
        return {"content": [{"type": "text", "text": "pong"}], "isError": False}
    return {"content": [{"type": "text", "text": "[오류] 없는 도구: %s" % name}],
            "isError": True}


def handle(req):
    """One request in -> result dict out. None = method not supported."""
    method = req.get("method", "")
    params = req.get("params") or {}
    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "my-law", "version": "0.1"},
        }
    if method == "ping":              # protocol-level liveness check (not our ping tool)
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        return call_tool(params.get("name", ""), params.get("arguments") or {})
    return None


def main():
    log("개인 실습용 도구입니다 (AI 세무실무 강의 실습) — 재배포 금지")
    for line in sys.stdin:            # one line = one JSON-RPC request
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue                  # ignore broken lines silently
        if "id" not in req:
            continue                  # notifications carry no id — never answer them
        result = handle(req)
        if result is None:
            resp = {"jsonrpc": "2.0", "id": req["id"],
                    "error": {"code": -32601,
                              "message": "지원하지 않는 요청: %s" % req.get("method", "")}}
        else:
            resp = {"jsonrpc": "2.0", "id": req["id"], "result": result}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()            # ship each line immediately


if __name__ == "__main__":
    main()
