import keyring
import json
from classes.services.slack_oauth_helpers import acquire_slack_oauth_tokens

class SlackTokens:
    def __init__(self, config:dict):
        self.slack_config = config.get("slack_oauth_config")
        
        self.service = self.slack_config.get("SERVICE")
        self.account = self.slack_config.get("ACCOUNT")

        self.slack_oauth_redirect_url = self.slack_config.get("SLACK_OAUTH_REDIRECT_URL")
        self.slack_client_id = self.slack_config.get("SLACK_CLIENT_ID")
        self.bot_scopes = self.slack_config.get("BOT_SCOPES")
        self.user_scopes = self.slack_config.get("USER_SCOPES")
        self.slack_team_id = self.slack_config.get("SLACK_TEAM_ID")

        self.slack_token = self.retrieve_token()

    def _create_token(self):
        slack_response_data = acquire_slack_oauth_tokens(self.slack_config)
        if slack_response_data and slack_response_data.get("ok"):

            team_id = slack_response_data.get("team").get("id")
            authed_user:dict = slack_response_data.get("authed_user")
            user_id = authed_user.get("id")
            user_token = authed_user.get("access_token")
            
            slack_user_data = {
                "team_id": team_id,
                "user_id": user_id,
                "user_token": user_token
            }

            return slack_user_data

    def retrieve_token(self):
        data = keyring.get_password(self.service, self.account)

        if not data:
            slack_user_token = self._create_token()
            self.set_token(slack_user_token)
            return slack_user_token          
        
        parsed_data = json.loads(data)
        return parsed_data

    def set_token(self, data: dict):
        try:
            data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            keyring.set_password(self.service, self.account, data)
            print(f'"{self.service}":"{self.account}" generated.')
        except Exception:
            raise Exception

    def delete(self):
        try:
            keyring.delete_password(self.service, self.account)
            print(f'"{self.service}" deleted.')
        except:
            print(f'"{self.account}" in "{self.service}" not found.')


