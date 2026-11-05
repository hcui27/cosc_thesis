"""Append-only log of every LLM call (generation or judging): model, prompt hash, tokens/cost, duration, outputs."""
import json, time, hashlib, pathlib

LEDGER = pathlib.Path("data/ledger.jsonl")

def log(kind, **fields):
    LEDGER.parent.mkdir(exist_ok=True)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind, **fields}
    if "prompt" in fields: rec["prompt_sha256"] = hashlib.sha256(fields["prompt"].encode()).hexdigest()[:16]
    with open(LEDGER, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

def usage_from_result(d):
    """Pull model, tokens and cost out of a claude stream-json/json 'result' object."""
    mu = d.get("modelUsage") or {}
    return {"models": list(mu), "total_cost_usd": d.get("total_cost_usd"), "duration_ms": d.get("duration_ms"),
            "num_turns": d.get("num_turns"), "is_error": d.get("is_error"),
            "tokens": {m: {k: v.get(k) for k in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")} for m, v in mu.items()}}
