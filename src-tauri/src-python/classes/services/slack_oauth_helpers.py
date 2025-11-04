# receive_once.py
import http.server, socketserver, json, os, threading, time, webbrowser, secrets
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def get_slack_user_token_via_ngrok(
    ngrok_https_base: str,
    *,
    port: int = 43110,
    path: str = "/receive-token",
    timeout_sec: int = 300,
    open_browser: bool = True,
) -> dict:
    """
    Executa o fluxo completo e retorna:
      {"ok": True, "user_token": "xoxp-...", "user_id": "U...", "team_id": "T..."}
    Parâmetros:
      ngrok_https_base: ex. "https://xxxxx.ngrok-free.app"
      port: porta do loopback (default 43110)
      path: caminho do receptor local (default "/receive-token")
      timeout_sec: tempo limite total (default 300s)
      open_browser: abre o navegador automaticamente (default True)
    Requer: seu backend com endpoint POST /init e callback em /auth/slack
    """
    ngrok_https_base = (ngrok_https_base or "").rstrip("/")
    if not (ngrok_https_base.startswith("https://")):
        raise ValueError("ngrok_https_base deve iniciar com https://")

    HOST = "127.0.0.1"
    CALLBACK_URL = f"http://{HOST}:{port}{path}"

    # --- sincronização para 1 único POST recebido ---
    done_event = threading.Event()
    result_holder = {"data": None, "error": None}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a, **k):  # silencia logs
            pass

        def _send(self, code=200, body=b"", ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            # CORS básico p/ fetch vindo de página https (ngrok)
            origin = self.headers.get("Origin", ngrok_https_base)
            self.send_header("Access-Control-Allow-Origin", origin or "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_OPTIONS(self):
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                return self._send(403, b'{"ok":false,"error":"forbidden"}')
            return self._send(204)

        def do_POST(self):
            # aceita só loopback
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                return self._send(403, b'{"ok":false,"error":"forbidden"}')

            if self.path != path:
                return self._send(404, b'{"ok":false,"error":"not_found"}')

            ctype = (self.headers.get("Content-Type") or "").lower()
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""

            try:
                if "application/json" in ctype:
                    data = json.loads(raw.decode("utf-8") or "{}")
                    token   = data.get("token") or data.get("user_token") or ""
                    user_id = data.get("user_id") or ""
                    team_id = data.get("team_id") or ""
                else:
                    from urllib.parse import parse_qs
                    qs = parse_qs(raw.decode("utf-8"))
                    token   = (qs.get("token") or qs.get("user_token") or [""])[0]
                    user_id = (qs.get("user_id") or [""])[0]
                    team_id = (qs.get("team_id") or [""])[0]
            except Exception:
                return self._send(400, b'{"ok":false,"error":"bad_payload"}')

            if not token:
                return self._send(400, b'{"ok":false,"error":"missing_user_token"}')

            payload = {"ok": True, "user_token": token, "user_id": user_id, "team_id": team_id}
            result_holder["data"] = payload
            done_event.set()

            return self._send(200, json.dumps(payload).encode("utf-8"))

    class Server(socketserver.TCPServer):
        allow_reuse_address = True

    # --- inicia servidor em thread ---
    srv = Server((HOST, port), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()

    try:
        # --- chama /init no backend ngrok ---
        state = secrets.token_urlsafe(24)
        init_url = ngrok_https_base + "/init"
        body = json.dumps({"state": state, "callback_url": CALLBACK_URL}).encode("utf-8")
        req = Request(init_url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=20) as r:
            init_resp = json.loads(r.read().decode("utf-8", "replace"))
        if not (init_resp.get("ok") and init_resp.get("auth_url")):
            raise RuntimeError(f"/init failed: {init_resp}")

        auth_url = init_resp["auth_url"]
        if open_browser:
            webbrowser.open(auth_url, new=1, autoraise=True)
        else:
            print("Abra a URL de autorização:", auth_url)

        # --- aguarda o POST do callback local ---
        if not done_event.wait(timeout_sec):
            raise TimeoutError("Timeout aguardando token no loopback")

        return result_holder["data"] or {"ok": False, "error": "no_data"}

    finally:
        try:
            srv.shutdown()
        except Exception:
            pass
        try:
            srv.server_close()
        except Exception:
            pass


# Uso direto (teste manual):
# if __name__ == "__main__":
#     NGROK = "https://52b222c4aea6.ngrok-free.app"  # <- troque aqui
#     data = get_slack_user_token_via_ngrok(NGROK, timeout_sec=300, open_browser=True)
    
