import json

def acquire_slack_oauth_tokens (
    config: dict,
    *,
    callback_host: str = "127.0.0.1",
    callback_port: int = 17123,
    callback_path: str = "/callback",
    timeout_sec: int = 60,
    open_browser: bool = True,
):
    """
    config esperado:
      {
        "SLACK_OAUTH_REDIRECT_URL": ".../exec",
        "SLACK_CLIENT_ID": "000.000",
        "BOT_SCOPES": "",
        "USER_SCOPES": "users:read,...",
        "SLACK_TEAM_ID": "TXXXX"   # opcional (enforce)
      }
    """
    import http.server, socketserver, threading, webbrowser
    import urllib.parse, urllib.request, secrets, time, json

    slack_oauth_url = config["SLACK_OAUTH_REDIRECT_URL"]
    slack_client_id = config["SLACK_CLIENT_ID"]
    bot_scopes      = config.get("BOT_SCOPES", "") or ""
    user_scopes     = config.get("USER_SCOPES", "") or ""
    team_enforce    = config.get("SLACK_TEAM_ID") or None

    state = secrets.token_hex(32)
    result = {"ok": False}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a, **k): return
        def _out(self, code, body):
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            try:
                self.wfile.write(body.encode("utf-8"))
            except Exception:
                pass  # navegador pode fechar a conexão

        def do_GET(self):
            nonlocal result
            p = urllib.parse.urlparse(self.path)
            if p.path != callback_path:
                return self._out(404, "Not Found")
            q = urllib.parse.parse_qs(p.query)
            ok   = q.get("ok", ["0"])[0] == "1"
            lid  = q.get("login_id", [""])[0]
            st   = q.get("state", [""])[0]
            team = q.get("team", [""])[0]
            if not ok or not lid or st != state:
                return self._out(400, "Invalid callback")
            if team_enforce and team and team != team_enforce:
                return self._out(403, "Workspace not allowed")

            fetch = f"{slack_oauth_url}?action=fetch&login_id={urllib.parse.quote(lid)}&state={urllib.parse.quote(state)}"
            with urllib.request.urlopen(fetch, timeout=30) as r:
                result = json.loads(r.read().decode("utf-8", "replace"))
            self._out(200, "<h3>OK</h3><p>Você já pode fechar esta janela.</p>")
            raise SystemExit  # encerra o loop do servidor

    class Server(socketserver.TCPServer):
        allow_reuse_address = True

    def serve_once():
        try:
            with Server((callback_host, callback_port), Handler) as httpd:
                while True:
                    try:
                        httpd.handle_request()
                    except SystemExit:
                        break
        except OSError as e:
            result.update(ok=False, error=f"bind_error:{e}")

    # monta URL de autorização (user-only se BOT_SCOPES vazio)
    params = {"client_id": slack_client_id, "redirect_uri": slack_oauth_url, "state": state}
    if bot_scopes.strip():  params["scope"] = bot_scopes
    if user_scopes.strip(): params["user_scope"] = user_scopes
    auth_url = "https://slack.com/oauth/v2/authorize?" + urllib.parse.urlencode(params)

    threading.Thread(target=serve_once, daemon=True).start()
    if open_browser: webbrowser.open(auth_url, new=1, autoraise=True)
    else: print("Abra a URL:", auth_url)

    deadline = time.time() + timeout_sec
    while time.time() < deadline and not result.get("ok"):
        time.sleep(0.15)

    if not result.get("ok"):
        raise TimeoutError("OAuth timeout ou erro no fetch do GAS.")
    return result



if __name__ == "__main__":

  config = {
      "SLACK_OAUTH_REDIRECT_URL": "https://script.google.com/macros/s/AKfycbxhopJPeY1Sl49yTRJPVSCI3liEZDejgF3wex63faSl4bgUgVN51rTrToL1ivl3iaqE/exec",
      "SLACK_CLIENT_ID": "549770083351.9075626247603",
      "BOT_SCOPES": "",
      "USER_SCOPES": "users:read,users:read.email,chat:write,files:write,channels:history,groups:history,groups:read,channels:read,reactions:write",
      "SLACK_TEAM_ID": "TG5NN2FAB"
  }

  data = acquire_slack_oauth_tokens(config)
  # print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
  if data and data.get("ok"):
      team_id = data.get("team").get("id")
      authed_user:dict = data.get("authed_user")
      user_id = authed_user.get("id")
      user_token = authed_user.get("access_token")
    
      # this will be stored on user local machine
      new_data = {
          "team_id": team_id,
          "user_id": user_id,
          "user_token": user_token
      }

      print(json.dumps(new_data, ensure_ascii=False, indent=2, default=str))
      
