"""Block until Wayback AND the Claude API answer (any HTTP response counts). A Mac that just woke from sleep, or a network blip, must not fail sites."""
import time, requests

def wait_for_net(max_wait=3600):
    t0 = time.time()
    while True:
        try:
            for u in ("https://web.archive.org/", "https://api.anthropic.com/"): requests.head(u, timeout=20, allow_redirects=True)
            return
        except requests.RequestException:
            if time.time() - t0 > max_wait: raise RuntimeError(f"network/Wayback unreachable for {max_wait}s")
            print("  waiting for network ...", flush=True); time.sleep(30)
