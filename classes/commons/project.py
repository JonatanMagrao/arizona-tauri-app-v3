from classes.core import ProjectTypeIdentifier
from classes.integrations.google_drive_helper import GoogleDriveHelper
from classes.commons import timer

def build_projects(config, glink: str):
    try:
        google_helper = GoogleDriveHelper(config)
        google_data = google_helper.get_link_data(glink)
        project_identifier = ProjectTypeIdentifier(config, google_data)
        return project_identifier.create_projects
    except Exception as e:
        raise e
    

def build_projects_from_links(config:dict,projects_links:list) -> list:
  projetos = []

  for link in projects_links:
      try:
        projeto = build_projects(config, link)
        projetos.append(projeto)
      except Exception as e:
        continue

  return projetos

def copy_projects(projetos:list):
  for projeto in projetos:
      try:
          projeto.dispatch_out()
      except Exception as e:
          continue

def notify_slack(projetos:list):
  for projeto in projetos:
      try:
          projeto.send_slack_message()
      except Exception as e:
          continue
