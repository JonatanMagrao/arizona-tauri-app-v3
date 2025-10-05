from classes.integrations.slack.slack_base import SlackBase
from classes.commons import long_path
from pathlib import Path

class SlackSuperplay(SlackBase):
    def __init__(self, *, raise_on_invalid: bool = True) -> None:
        super().__init__()

    def send_file_to_channels(self, channel_ids: list[str], file_path: Path, msg_text: str = "") -> None:
        file_path = long_path(Path(file_path))

        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return

        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
                file_name = file_path.name

            for channel_id in channel_ids:
                try:
                    response = self.client.files_upload_v2(
                        channel=channel_id,
                        file=file_content,
                        filename=file_name,
                        title="",
                        initial_comment=msg_text
                    )

                    channel_name = self.get_channel_name_by_id(channel_id)
                    print(
                        f"✅ File: {response['file']['name']} sent to channel: #{channel_name}")

                except Exception as e:
                    raise e

        except Exception as e:
            raise e

    def send_out_msg(self, slack_channel, producers, project_name, project_link, project_file):
        producers = self.mark_users(producers)
        out_msg = f"{producers}\n{project_name}\n{project_link}"
        self.send_file_to_channels([slack_channel], project_file, out_msg)


if __name__ == "__main__":
    slack = SlackSuperplay()

    channel_id = "C093YV2DSFK"
    producers = ['andrei.sm@superplay.co', 'jonatan.m@superplay.co']
    project_name = "DS-V-002-056_Scenes_Beast_Revised_DS-H-013-003_EN_30s"
    project_link = "https://drive.google.com/open?id=1hYoyBj6E8-7dcb_RvTglKRj6JAhAKPLm&usp=drive_fs"
    video_path = r"G:\Drives compartilhados\Marketing OUT\DS_DisneySolitaire_OUT\07-Videos\EN\DS-V-002_Scenes\DS-V-002-056_Scenes_Beast_Revised_DS-H-013-003_EN_30s\DS-V-002-056_Scenes_Beast_Revised_DS-H-013-003_EN_30s_1080x1080.mp4"

    slack.send_out_msg(channel_id, producers, project_name, project_link, video_path)