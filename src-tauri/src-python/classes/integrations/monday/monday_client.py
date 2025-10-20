import requests
import json
import re
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urlparse  # <-- necessário para parsear a URL do Monday
import os


class MondayClient:
    API_URL = "https://api.monday.com/v2"

    # padrões de parsing
    _STATUS_UPDATED_RE = re.compile(r"updated to\s+(.+?)\s+by\s+(.+)", re.IGNORECASE | re.DOTALL)
    _STATUS_MARKED_RE  = re.compile(r"marked as\s+(.+?)\s+by\s+(.+)",  re.IGNORECASE | re.DOTALL)
    _GDRIVE_RE = re.compile(r"(?P<url>(?:https?://)?(?:drive|docs)\.google\.com/\S+)",re.IGNORECASE)

    def __init__(self, config:dict, api_url: Optional[str] = None):
        self.api_key = config.get("monday_config")["MONDAY_TOKEN"]
        self.api_url = api_url or self.API_URL
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            # "API-Version": "2024-10",  # opcional: fixe versão se quiser estabilidade global
        }
        # contexto interno do item selecionado
        self._board_id: Optional[int] = None
        self._pulse_id: Optional[int] = None

    # ------------- infra -------------
    def _run_query(self, query: str, api_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa uma query GraphQL. Se api_version for informado, usa um header 'API-Version' apenas nesta chamada.
        """
        headers = self.headers if not api_version else {**self.headers, "API-Version": api_version}
        resp = requests.post(self.api_url, headers=headers, json={"query": query}, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        if "errors" in payload:
            # propaga a primeira mensagem de erro de GraphQL
            raise RuntimeError(payload["errors"])
        return payload["data"]

    # ------------- helpers internos -------------
    @staticmethod
    def _display_name(creator: Optional[Dict[str, Any]]) -> str:
        return (creator or {}).get("name") or "monday.com automation"

    @classmethod
    def _parse_status_change(cls, text: str, fallback_author: str):
        if not text:
            return None
        m = cls._STATUS_UPDATED_RE.search(text) or cls._STATUS_MARKED_RE.search(text)
        if not m:
            return None
        status = m.group(1).strip()
        who    = m.group(2).strip() or fallback_author
        return (status, who)

    @classmethod
    def _extract_gdrive_links(cls, text: str):
        if not text:
            return []
        links = []
        for u in cls._GDRIVE_RE.findall(text):
            links.append(u.rstrip(").,;"))
        # dedup preservando ordem
        seen, out = set(), []
        for u in links:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    @staticmethod
    def _get_monday_ids(url: str) -> Tuple[int, int]:
        """
        Retorna (board_id, item_id) a partir de uma URL do Monday.
        Aceita segmentos extras entre boards/<id> e (pulses|items)/<id> (ex.: views/<id>, posts/<id>, etc.).
        """
        u = urlparse(url)
        if u.netloc.lower() != "superplay.monday.com":
            raise ValueError("Invalid domain (expected superplay.monday.com)")

        # Casa caminho do tipo: /boards/523.../[...]/(pulses|items)/1811...[/...]
        m = re.search(
            r"/boards/(\d+)(?:/[^/]+)*/(?:pulses|items)/(\d+)(?:/|$)",
            u.path,
            flags=re.IGNORECASE,
        )
        if not m:
            raise ValueError("Invalid Monday path (boards/<id> ... (pulses|items)/<id> not found)")

        board_id, item_id = map(int, m.groups())
        return board_id, item_id

    def use_item_url(self, url: str) -> Tuple[int, int]:
        """
        Vincula o contexto interno (board_id, pulse_id) a partir de uma URL do Monday.
        Ex.: client.use_item_url("https://superplay.monday.com/boards/123456789/items/987654321")
        """
        b_id, p_id = self._get_monday_ids(url)
        self._board_id = b_id
        self._pulse_id = p_id

        return b_id, p_id

    def _ensure_context(self):
        if self._board_id is None or self._pulse_id is None:
            raise ValueError("Contexto de item não definido. Chame use_item_url(...) primeiro.")

    def _get_item_name(self, pulse_id: int) -> str:
        q = f"""
        {{
          items (ids: [{pulse_id}]) {{
            id
            name
          }}
        }}
        """
        data = self._run_query(q)
        items = data.get("items", [])
        return (items[0].get("name") if items else None) or "(sem nome)"

    def _get_updates_raw(self, pulse_id: int):
        q = f"""
        {{
          items (ids: [{pulse_id}]) {{
            id
            name
            updates (limit: 250) {{
              id
              text_body
              created_at
              creator {{ id name }}
              replies {{
                id
                text_body
                created_at
                creator {{ id name }}
              }}
            }}
          }}
        }}
        """
        data = self._run_query(q)
        items = data.get("items", [])
        return items[0]["updates"] if items else []

    def _find_status_column_id(self, board_id: int, title_hint: Optional[str] = None) -> str:
        q = f"""
        {{
          boards(ids: {board_id}) {{
            id
            columns {{
              id
              title
              type
            }}
          }}
        }}
        """
        data = self._run_query(q)
        boards = data.get("boards", [])
        if not boards:
            raise RuntimeError("Board não encontrado.")
        cols = boards[0].get("columns", [])

        status_cols = [c for c in cols if c.get("type") == "status"]

        if title_hint:
            hint = title_hint.lower()
            for c in status_cols:
                t = (c.get("title") or "").lower()
                if t == hint or hint in t:
                    return c["id"]

        if status_cols:
            return status_cols[0]["id"]

        for c in cols:
            if (c.get("title") or "").lower() == "status":
                return c["id"]

        raise RuntimeError("Nenhuma coluna de status foi encontrada neste board.")

    # ------------- métodos públicos -------------

    # -- (1) Novo nome semântico e sem parâmetros --
    def get_updates_summary(self) -> Dict[str, Any]:
        """
        Retorna um dicionário com resumo das atualizações do item corrente (self._pulse_id):
        {
          "item_name": "<nome>",
          "status_changes": [{"ts": "...", "status_change": "...", "status_changed_by": "..."}],
          "gdrive_links":  [{"ts": "...", "gdurl": "...", "by": "..."}]
        }
        """
        self._ensure_context()
        # reutiliza a lógica existente, agora com IDs internos
        return self.get_status_and_gdrive_dict(self._board_id, self._pulse_id)

    # Mantém para compatibilidade (assinatura antiga).
    # OBS: Apesar do nome antigo, internamente só precisa do pulse_id mesmo.
    def get_status_and_gdrive_dict(self, board_id: int, pulse_id: int) -> Dict[str, Any]:
        """
        Retorna:
        {
          "item_name": "<nome>",
          "status_changes": [{"ts": "...", "status_change": "...", "status_changed_by": "..."}],
          "gdrive_links":  [{"ts": "...", "gdurl": "...", "by": "..."}]
        }
        """
        item_name = self._get_item_name(pulse_id)
        updates = self._get_updates_raw(pulse_id)

        status_events: List[Dict[str, Any]] = []
        gdrive_links:  List[Dict[str, Any]] = []

        for u in updates:
            u_ts   = u.get("created_at", "")
            u_txt  = (u.get("text_body") or "").strip()
            u_who  = self._display_name(u.get("creator"))

            sc = self._parse_status_change(u_txt, u_who)
            if sc:
                status_events.append({
                    "ts": u_ts,
                    "status_change": sc[0],
                    "status_changed_by": sc[1]
                })

            for link in self._extract_gdrive_links(u_txt):
                gdrive_links.append({
                    "ts": u_ts,
                    "gdurl": link,
                    "by": u_who
                })

            for r in (u.get("replies") or []):
                r_ts  = r.get("created_at", "")
                r_txt = (r.get("text_body") or "").strip()
                r_who = self._display_name(r.get("creator"))

                sc_r = self._parse_status_change(r_txt, r_who)
                if sc_r:
                    status_events.append({
                        "ts": r_ts,
                        "status_change": sc_r[0],
                        "status_changed_by": sc_r[1]
                    })

                for link in self._extract_gdrive_links(r_txt):
                    gdrive_links.append({
                        "ts": r_ts,
                        "gdurl": link,
                        "by": r_who
                    })

        status_events.sort(key=lambda x: x["ts"])
        gdrive_links.sort(key=lambda x: x["ts"])

        return {
            "item_name": item_name,
            "status_changes": status_events,
            "gdrive_links": gdrive_links
        }

    # -- (2) get_current_status: manter assinatura original --
    def get_current_status(self,
                           column_title_hint: Optional[str] = None,
                           column_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retorna o status atual da task:
        {
          "column_id": "status_1",
          "label": "Sent To Marketing",
          "label_id": 7,
          "color": "#F6C23E"
        }
        """
        board_id = self._board_id
        pulse_id = self._pulse_id
        # resolve column_id da coluna de status
        col_id = column_id or self._find_status_column_id(board_id, column_title_hint)

        # pega o valor atual da coluna no item
        q_item = f"""
        {{
          items(ids: [{pulse_id}]) {{
            id
            column_values(ids: ["{col_id}"]) {{
              id
              text
              value
            }}
          }}
        }}
        """
        data_item = self._run_query(q_item)
        items = data_item.get("items", [])
        if not items or not items[0].get("column_values"):
            return {"column_id": col_id, "label": None, "label_id": None, "color": None}

        cv = items[0]["column_values"][0]
        label_text = cv.get("text")
        label_id = None
        try:
            raw = json.loads(cv.get("value") or "{}")
            # para coluna status, geralmente {"index": <int>}
            label_id = raw.get("index")
        except Exception:
            label_id = None

        # pega a cor nas settings da coluna do board
        q_board = f"""
        {{
          boards(ids: {board_id}) {{
            id
            columns {{
              id
              type
              settings_str
            }}
          }}
        }}
        """
        data_board = self._run_query(q_board)
        color = None
        boards = data_board.get("boards", [])
        if boards:
            for col in boards[0].get("columns", []):
                if col.get("id") == col_id and col.get("type") == "status":
                    try:
                        settings = json.loads(col.get("settings_str") or "{}")
                        # labels_colors: {"5": {"color":"#...","border":"#..."}}
                        if label_id is not None:
                            color = (settings.get("labels_colors") or {}).get(str(label_id), {}).get("color")
                    except Exception:
                        pass
                    break

        return {
            "column_id": col_id,
            "label": label_text,
            "label_id": label_id,
            "color": color,
        }

    # -- (3) set_item_status: usa contexto interno (sem board_id/pulse_id como parâmetros) --
    def set_item_status(self, status_label: str,
                        column_id: Optional[str] = None,
                        column_title_hint: Optional[str] = None) -> None:
        """
        Altera o status da task ligada no contexto interno para o rótulo informado (ex.: "Done", "WIP", ...).
        """
        self._ensure_context()
        col_id = column_id or self._find_status_column_id(self._board_id, column_title_hint)
        value_json = json.dumps({"label": status_label})  # {"label": "Done"} etc.

        q = f"""
        mutation {{
          change_column_value(
            board_id: {self._board_id},
            item_id: {self._pulse_id},
            column_id: {json.dumps(col_id)},
            value: {json.dumps(value_json)}
          ) {{
            id
          }}
        }}
        """

        try:
          self._run_query(q)
        except Exception as e:
          raise RuntimeError(f"Error on updating status: {e}")

    # ------------------------- NOVOS MÉTODOS -------------------------

    @staticmethod
    def _extract_people_ids(value_raw: Optional[str]) -> list[int]:
        """Extrai IDs de usuários de uma coluna People (value JSON)."""
        if not value_raw:
            return []
        try:
            o = json.loads(value_raw)
        except Exception:
            return []
        ids: list[int] = []
        for p in o.get("personsAndTeams", []):
            if p.get("kind") == "person" and isinstance(p.get("id"), int):
                ids.append(p["id"])
        for p in o.get("people", []):
            if isinstance(p.get("id"), int):
                ids.append(p["id"])
        # dedup preservando ordem
        seen, out = set(), []
        for i in ids:
            if i not in seen:
                seen.add(i); out.append(i)
        return out

    def get_parent_pulse(self, pulse_id: int, parent_connect_title: str = "Parent Connect") -> Optional[int]:
        """
        Retorna o primeiro pulse ligado no Parent Connect do item informado.
        Se não houver vínculo, retorna None.
        """
        # descobrir board do item
        q_bfi = f"""
        {{
          items(ids: [{pulse_id}]) {{ board {{ id }} }}
        }}
        """
        d_bfi = self._run_query(q_bfi)
        items = d_bfi.get("items", [])
        if not items:
            return None
        board_id = int(items[0]["board"]["id"])

        # localizar coluna board_relation pelo título exato
        q_cols = f"""
        {{
          boards(ids: {board_id}) {{
            columns {{ id title type }}
          }}
        }}
        """
        d_cols = self._run_query(q_cols)
        cols = (d_cols.get("boards") or [{}])[0].get("columns", [])
        col = next((c for c in cols if c.get("type") == "board_relation" and (c.get("title") or "").strip() == parent_connect_title.strip()), None)
        if not col:
            return None

        # ler linked_item_ids via fragmento tipado
        q_rel = f"""
        {{
          items(ids: [{pulse_id}]) {{
            column_values(ids: ["{col['id']}"]) {{
              ... on BoardRelationValue {{ linked_item_ids }}
            }}
          }}
        }}
        """
        d_rel = self._run_query(q_rel)
        cv = (d_rel.get("items") or [{}])[0].get("column_values") or []
        ids = (cv[0] or {}).get("linked_item_ids") if cv else None
        if not ids:
            return None
        try:
            return int(ids[0])
        except Exception:
            return None

    def get_people_mk_owner_by_pulse(self, pulse_id: int, title: str = "People: MK Owner") -> list[dict]:
        """
        Retorna uma lista de dicts com {name, email} da coluna People 'People: MK Owner' do item.
        Ex.: [{ "name": "...", "email": "..." }, ...]
        """
        # descobrir board do item
        q_bfi = f"""
        {{
          items(ids: [{pulse_id}]) {{ board {{ id }} }}
        }}
        """
        d_bfi = self._run_query(q_bfi)
        items = d_bfi.get("items", [])
        if not items:
            return []
        board_id = int(items[0]["board"]["id"])

        # localizar coluna People pelo título exato
        q_cols = f"""
        {{
          boards(ids: {board_id}) {{
            columns {{ id title type }}
          }}
        }}
        """
        d_cols = self._run_query(q_cols)
        cols = (d_cols.get("boards") or [{}])[0].get("columns", [])
        col = next((c for c in cols if c.get("type") == "people" and (c.get("title") or "").strip() == title.strip()), None)
        if not col:
            return []

        # ler valor da coluna no item e extrair user_ids
        q_val = f"""
        {{
          items(ids: [{pulse_id}]) {{
            column_values(ids: ["{col['id']}"]) {{ value }}
          }}
        }}
        """
        d_val = self._run_query(q_val)
        cv = (d_val.get("items") or [{}])[0].get("column_values") or []
        value_raw = (cv[0] or {}).get("value") if cv else None
        user_ids = self._extract_people_ids(value_raw)
        if not user_ids:
            return []

        # mapear ids -> {name, email}
        q_users = f"""
        {{
          users(ids: {json.dumps(user_ids)}) {{ id name email }}
        }}
        """
        d_users = self._run_query(q_users)
        by_id = {int(u["id"]): {"name": u.get("name"), "email": u.get("email")} for u in (d_users.get("users") or [])}

        # preservar ordem e deduplicar por id
        seen, out = set(), []
        for uid in user_ids:
            if uid in by_id and uid not in seen:
                seen.add(uid); out.append(by_id[uid])
        return out

    # -- (4) get_mkt_owners: agora usa contexto interno --
    def get_mkt_owners(self) -> list[dict]:
        self._ensure_context()
        parent_pulse = self.get_parent_pulse(self._pulse_id)
        if not parent_pulse:
            return []
        mk_contacts = self.get_people_mk_owner_by_pulse(parent_pulse)
        return mk_contacts

    # -- (5) Novo: links do Google Drive do update "pinado" --
    def get_pinned_update_gdrive_links(self) -> List[Dict[str, Any]]:
        """
        Retorna todos os links de Google Drive (drive.google.com) presentes no update pinado
        ao topo do item atual (self._pulse_id). Se não houver update pinado, retorna [].

        Formato:
        [
          {"ts": "<created_at>", "gdurl": "<url>", "by": "<autor>", "update_id": "<id>"},
          ...
        ]
        """
        self._ensure_context()
        # Precisamos do campo pinned_to_top -> disponível a partir de API-Version 2024-10
        q = f"""
        {{
          items (ids: [{self._pulse_id}]) {{
            id
            name
            updates (limit: 100) {{
              id
              text_body
              created_at
              creator {{ id name }}
              pinned_to_top {{ item_id }}
            }}
          }}
        }}
        """
        data = self._run_query(q, api_version="2024-10")
        items = data.get("items", [])
        if not items:
            return []

        updates = items[0].get("updates") or []
        # updates vêm em ordem decrescente (mais recente primeiro) segundo a documentação
        # Encontrar o primeiro update que esteja pinado neste item específico
        pinned_update = None
        pid_str = str(self._pulse_id)
        for u in updates:
            pins = u.get("pinned_to_top") or []
            # o schema documenta 'item_id' em cada pin
            if any(str(pin.get("item_id")) == pid_str for pin in pins):
                pinned_update = u
                break

        if not pinned_update:
            return []

        ts = pinned_update.get("created_at") or ""
        by = self._display_name(pinned_update.get("creator"))
        urls = self._extract_gdrive_links((pinned_update.get("text_body") or "").strip())

        return [{"ts": ts, "gdurl": url, "by": by, "update_id": pinned_update.get("id")} for url in urls]


# --------------------
# Exemplo de uso (opcional)
# --------------------
if __name__ == "__main__":
    MONDAY_TOKEN = os.getenv("MONDAY_TOKEN")
    client = MondayClient(MONDAY_TOKEN)

    # Vincula o item pelo link do Monday (aceita .../pulses/<id> ou .../items/<id>)
    MONDAY_URL = "https://superplay.monday.com/boards/5239196091/pulses/18147479560/posts/4566449807"
    client.use_item_url(MONDAY_URL)

    # 1) Resumo das atualizações do item (novo nome, sem parâmetros)
    # d = client.get_updates_summary()
    # print(json.dumps(d, ensure_ascii=False, indent=2))

    # 2) Status atual (mantido com assinatura original)
    # cur = client.get_current_status(column_title_hint="Task Status")
    # print("Status atual:", cur)

    # 3) Alterar status (agora sem board_id/pulse_id)
    # client.set_item_status("Sent to Marketing", column_title_hint="Task Status")
    # print("Status alterado.")

    # 4) Donos de Marketing via Parent (agora sem passar pulse_id)
    mkt_owners = client.get_mkt_owners()
    # print(json.dumps(mkt_owners, ensure_ascii=False, indent=2))
    saida = [item["email"] for item in mkt_owners]
    print(saida)

    # 5) Links de Google Drive do update pinado
    # pinned_links = client.get_pinned_update_gdrive_links()
    # print(json.dumps(pinned_links, ensure_ascii=False, indent=2))
