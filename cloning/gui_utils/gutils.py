import os
import re
import json
from gui_utils.project import Project


def project_exists(project_name):
    return os.path.isdir(os.path.join("projects", project_name))

def check_project_name(project_name):
    #cannot contain spaces, cannot be empty, and no special characters
    #Use regex
    if not project_name:
        return False
    if re.search(r'\s', project_name):
        return False
    if re.search(r'[^\w]', project_name):
        return False
    return True

def create_project(project_name) -> Project:
    os.makedirs(os.path.join("projects"), exist_ok=True)
    return Project(project_name, os.path.join("projects", project_name))

def save_project(project):
    with open(os.path.join(project.directory, "metadata.json"), "w") as f:
        f.write(project.toJSON())

def load_project(project_file_path) -> Project:
    with open(project_file_path) as f:
        data = json.load(f)
    return Project.fromJSON(json.dumps(data))

def get_last_sentence(project_file):
    with open(project_file) as f:
        data = json.load(f)
    return data["audios"][-1]["sentence"]

# if __name__ == "__main__":
#     print(check_project_name(sys.argv[1]))