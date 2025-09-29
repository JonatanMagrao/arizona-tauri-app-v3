from classes.GoogleDriveHelper import GoogleDriveHelper
from classes.ProjectTypeIdentifier import ProjectTypeIdentifier

def build_projects(config, glink: str):
    try:
        google_helper = GoogleDriveHelper(config)
        google_data = google_helper.get_link_data(glink)
        project_identifier = ProjectTypeIdentifier(config, google_data)
        return project_identifier.create_projects
    except Exception as e:
        raise e


def get_full_metadata(project_list: list):
    project_metadata = []
    for projeto in project_list:
        try:
            project_metadata.append(projeto.job_manifest)
        except Exception as e:
            print(f"Error processing project: {e}")
            continue
    return project_metadata


def collect_copy_paths(job_manifest: list[dict]):
    try:
        project_tasks = []
        for item in job_manifest:
            project_tasks.append(item.get("copy_paths"))

        return project_tasks
    except Exception as e:
        raise e