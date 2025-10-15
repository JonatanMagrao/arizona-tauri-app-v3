from classes.core import ProjectTypeIdentifier
from classes.integrations.google_drive_helper import GoogleDriveHelper
from classes.integrations.monday.monday_client import MondayClient
from classes.core.superplay_project import SuperplayProject
import re
import traceback


def build_projects(config, project_url: str):

    # todo criar validador para os links. eles vão aceitar tanto os links da monday quanto os links do google
    try:
        google_helper = GoogleDriveHelper(config)
        google_data = google_helper.get_link_data(project_url)
        project_identifier = ProjectTypeIdentifier(config, google_data)
        projetos = project_identifier.create_projects
        return projetos
    except Exception as e:
        raise e


def build_projects_from_links(config: dict, projects_links: list) -> list:

    projetos = []

    monday_client = MondayClient(config)
    monday_url = re.compile(r"https://superplay.monday.com/boards")

    for link in projects_links:

        try:

            if monday_url.match(link):
                monday_client.use_item_url(link)
                monday_links = [item["gdurl"]
                                for item in monday_client.get_pinned_update_gdrive_links()]

                if len(monday_links) == 0:
                    projetos.append(
                        {"status":"error","msg": f"No gdrive links found on pinned updates on: {link}"})
                    continue

                mkt_owners = [owner["email"]
                              for owner in monday_client.get_mkt_owners()]

                for monday_link in monday_links:
                    projeto = build_projects(config, monday_link)
                    projeto.producer_list = mkt_owners
                    projetos.append(projeto)

            else:

                projeto = build_projects(config, link)
                projetos.append(projeto)

        except Exception as e:
            projetos.append({"status":"error","msg": str(e)})
            continue
            # raise e

    return projetos


def copy_projects(projetos: list[SuperplayProject]):
    response = []
    for projeto in projetos:
        if isinstance(projeto, dict) and projeto["status"] == "error":
            continue
        try:
            metadata = projeto.dispatch_out()
            response.append(metadata)
        except Exception as e:
            continue

    return response


def notify_slack(projetos: list):
    response = []
    for projeto in projetos:
        if isinstance(projeto, dict) and projeto["status"] == "error":
            continue
        try:
            slack_metadata = projeto.send_slack_message()
            response.append(slack_metadata)
        except Exception as e:
            response.append({"status":"error","msg": str(e)})
            continue
        
    return response


def generate_project_metadata(projetos: list):
    manifest_list = []
    for projeto in projetos:
        try:
            if isinstance(projeto, dict) and projeto["status"] == "error":
                manifest_list.append({"status":"error","msg": projeto["msg"]})
                continue

            manifesto = projeto.job_manifest
            for item in manifesto:
                manifest_list.append(item)
        except Exception as e:
            manifest_list.append({"status":"error","msg": str(e)})
            continue

    return manifest_list
