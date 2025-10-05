from classes.core import ProjectTypeIdentifier
from classes.integrations.google_drive_helper import GoogleDriveHelper

def build_projects(config, glink: str):
    try:
        google_helper = GoogleDriveHelper(config)
        google_data = google_helper.get_link_data(glink)
        project_identifier = ProjectTypeIdentifier(config, google_data)
        return project_identifier.create_projects
    except Exception as e:
        raise e