import os
import re
import json
import shutil
import pandas as pd

from cloning.gui_utils.project import Project

sentences: pd.DataFrame = pd.DataFrame()


def project_exists(project_name):
    return os.path.isdir(os.path.join("projects", project_name))


def check_project_name(project_name):
    # cannot contain spaces, cannot be empty, and no special characters
    # Use regex
    if not project_name:
        return False
    if re.search(r'\s', project_name):
        return False
    if re.search(r'[^\w]', project_name):
        return False
    return True


def create_project(project_name) -> Project:
    os.makedirs(os.path.join("projects", "TEMP", "wavs"))
    return Project(project_name, os.path.join("projects", project_name))


def save_project(project):
    shutil.move(os.path.join("projects", "TEMP"), project.directory)
    with open(os.path.join(project.directory, "metadata.json"), "w", encoding="utf8") as f:
        f.write(project.toJSON())


def load_project(project_file_path) -> Project:
    with open(project_file_path) as f:
        data = json.load(f)
    return Project.fromJSON(json.dumps(data))


def get_last_sentence(project_file):
    with open(project_file) as f:
        data = json.load(f)
    return data["audios"][-1]["sentence"]


def get_first_sentence() -> str:
    global sentences
    sentences = pd.read_csv("validated_cleaned.tsv", sep="\t")
    return sentences.sample()["sentence"].values[0]


def save_current_audio(project: Project, current_sentence: str):
    shutil.move(os.path.join("projects", "TEMP", "tempfile.wav"),
                os.path.join("projects", "TEMP", "wavs", str(project.current_audio_index()) + ".wav"))
    project.add_audio(current_sentence)


def get_new_sentence():
    return sentences.sample()["sentence"].values[0]


def remove_temp_folder():
    if os.path.isdir(os.path.join("projects", "TEMP")):
        shutil.rmtree(os.path.join("projects", "TEMP"))

# if __name__ == "__main__":
#     print(check_project_name(sys.argv[1]))
