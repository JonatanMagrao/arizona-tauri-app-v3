from __future__ import annotations

from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from classes.integrations.slack.slack_tokens import SlackTokens


class SlackBase:

    def __init__(self, config: dict) -> None:
        # pega o token direto do KeyVault
        self.slack_config = SlackTokens(config)
        self.token = self.slack_config.retrieve_token()["user_token"]

        self.client = WebClient(token=self.token)
        self._is_valid: Optional[bool] = None

        if not self.validate_token():
            raise ValueError("Slack user token inválido (auth_test falhou).")

    def validate_token(self) -> bool:
        """Retorna True se o token for válido (auth_test OK)."""
        try:
            resp = self.client.auth_test()
            self._is_valid = bool(resp.get("user_id"))
        except SlackApiError:
            self._is_valid = False
        return bool(self._is_valid)

    def get_user_info_by_id(self, user_id: str) -> dict | None:
        """
        Retorna:
        {
            "user_id": <str>,
            "name": <legacy username>,
            "real_name": <str | None>,
            "display_name": <str | None>,
            "email": <str | None>,
            "team": {"id": ..., "name": ..., "domain": ...} | {"id": ...} | None
        }
        Escopos: users:read, users:read.email (p/ email), team:read (p/ name/domain)
        """
        try:
            resp = self.client.users_info(user=user_id)
            user = resp.get("user", {}) or {}
            profile = user.get("profile", {}) or {}

            team_data = None
            # Tenta obter informações completas do workspace do token
            try:
                t = self.client.team_info().get("team", {}) or {}
                if t:
                    team_data = {
                        "id": t.get("id"),
                        "name": t.get("name"),
                        "domain": t.get("domain"),
                    }
            except SlackApiError:
                # fallback mínimo usando possível team_id do objeto user
                tid = user.get("team_id")
                if tid:
                    team_data = {"id": tid}

            return {
                "user_id": user.get("id") or user_id,
                "name": user.get("name"),  # legacy username
                "real_name": profile.get("real_name"),
                "display_name": profile.get("display_name") or profile.get("display_name_normalized"),
                "email": profile.get("email"),
                "team": team_data,
            }
        except SlackApiError:
            return None

    def get_user_name_by_id(
        self,
        user_id: str,
        *,
        prefer_display_name: bool = True,
    ) -> Optional[str]:
        """Retorna o display_name ou real_name para um user_id."""
        try:
            resp = self.client.users_info(user=user_id)
            user = resp.get("user", {}) or {}
            profile = user.get("profile", {}) or {}
            display = profile.get("display_name") or profile.get(
                "display_name_normalized")
            real = profile.get("real_name") or profile.get(
                "real_name_normalized")
            if prefer_display_name and display:
                return display
            return display or real or None
        except SlackApiError:
            return None

    def get_channel_name_by_id(self, channel_id: str) -> Optional[str]:
        """Retorna o nome do canal (sem '#') para um channel_id."""
        try:
            resp = self.client.conversations_info(channel=channel_id)
            ch = resp.get("channel", {}) or {}
            return ch.get("name")
        except SlackApiError:
            return None

    def get_user_id_by_email(self, email: str) -> Optional[str]:
        """
        Retorna o user_id a partir do e-mail.
        Requer escopo: users:read.email (além de users:read).
        """
        try:
            resp = self.client.users_lookupByEmail(email=email)
            user = resp.get("user", {}) or {}
            return user.get("id")
        except SlackApiError:
            return None

    def user_id_list_by_email(self, email_list: list) -> list:
        user_id_list = []
        for email in email_list:
            user_id = self.get_user_id_by_email(email)
            if user_id:
                user_id_list.append(user_id)
        return user_id_list

    def send_message_to_channel(
        self,
        channel_id: str,
        text: str,
        *,
        thread_ts: Optional[str] = None,
    ) -> Optional[str]:
        """
        Envia mensagem para um canal (channel_id). Retorna o ts da mensagem ou None em erro.
        Requer escopo: chat:write (no user token).
        """
        try:
            resp = self.client.chat_postMessage(
                channel=channel_id,
                text=text,
                thread_ts=thread_ts,
            )
            return resp.get("ts")
        except SlackApiError:
            return None

    def send_dm_by_email(
        self,
        email: str,
        text: str,
        *,
        thread_ts: Optional[str] = None,
    ) -> Optional[str]:
        """
        Envia DM para um usuário a partir do e-mail. Retorna o ts da mensagem ou None em erro.
        Requer escopos: users:read.email, chat:write, im:write (dependendo da configuração).
        """
        try:
            # 1) resolve user_id pelo e-mail
            u = self.client.users_lookupByEmail(
                email=email).get("user", {}) or {}
            user_id = u.get("id")
            if not user_id:
                return None
            # 2) abre (ou reutiliza) a conversa IM
            im = self.client.conversations_open(users=user_id)
            im_channel = (im.get("channel") or {}).get("id")
            if not im_channel:
                return None
            # 3) envia a mensagem
            resp = self.client.chat_postMessage(
                channel=im_channel,
                text=text,
                thread_ts=thread_ts,
            )
            return resp.get("ts")
        except SlackApiError:
            return None

    def mark_users(self, user_email: list) -> str | None:
        if not user_email:
            return None
        return ' '.join(f"<@{self.get_user_id_by_email(user_id)}>" for user_id in user_email)


# -------------------------
# Uso rápido (exemplo)
# -------------------------
if __name__ == "__main__":
    config = {
        "slack_config": {
            "SLACK_OAUTH_REDIRECT_URL": "https://script.google.com/macros/s/AKfycbxhopJPeY1Sl49yTRJPVSCI3liEZDejgF3wex63faSl4bgUgVN51rTrToL1ivl3iaqE/exec",
            "SLACK_CLIENT_ID": "549770083351.9075626247603",
            "BOT_SCOPES": "",
            "USER_SCOPES": "users:read,users:read.email,chat:write,files:write,channels:history,groups:history,groups:read,channels:read,reactions:write",
            "SLACK_TEAM_ID": "TG5NN2FAB",
            "SERVICE": "com.superplay.slack.oauth.out-process",
            "ACCOUNT": "user.data"
        }
    }
    slack = SlackBase(config)

    # print("Token válido?", slack.validate_token())
    # print(slack.mark_users("andrei.sm@superplay.co"))

    # user_id = slack.get_user_id_by_email("shachargr@superplay.co")
    # print(user_id)

    # user_info = slack.get_user_info_by_id("U046PNH7RQQ")
    # print(json.dumps(user_info, indent=2, ensure_ascii=False, default=str))

    # channel_name = slack.get_channel_name_by_id("C08UDRZF9GC")
    # print("channel_name:", channel_name)

    # slack.send_message_to_channel("C093YV2DSFK", f"{slack.mark_users(['andrei.sm@superplay.co'])} teste")
    # ts = slack.send_dm_by_email("jonatan.m@superplay.co", f"{slack.mark_users(['andrei.sm@superplay.co','jonatan.m@superplay.co'])}\nteste")
    # print(slack.mark_users(['andrei.sm@superplay.co','jonatan.m@superplay.co']))

    # print(slack.user_id_list_by_email(['andrei.sm@superplay.co','jonatan.m@superplay.co']))
    # print(slack.mark_users(
    #     ['andrei.sm@superplay.co', 'jonatan.m@superplay.co']))
