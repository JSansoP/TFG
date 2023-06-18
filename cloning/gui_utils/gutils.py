import csv
import json
import os
import random
import re
import shutil

from .project import Project

sentences = list()


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
    if os.path.isfile(os.path.join("projects", "TEMP", "tempfile.wav")):
        shutil.move(os.path.join("projects", "TEMP", "tempfile.wav"), os.path.join("projects", "TEMP", "wavs",
                                                                                   str(project.next_audio_index()) + ".wav"))
    shutil.copytree(os.path.join("projects", "TEMP"), project.directory, dirs_exist_ok=True)
    with open(os.path.join(project.directory, "metadata.json"), "w", encoding="utf8") as f:
        f.write(project.to_json())


def open_project(project_file_path) -> Project:
    with open(project_file_path, "r", encoding='utf8') as f:
        data = json.load(f)
    return Project.from_json(json.dumps(data))


def get_last_sentence(project_file):
    with open(project_file) as f:
        data = json.load(f)
    return data["audios"][-1]["sentence"]


def get_first_sentence() -> str:
    global sentences
    with open("validated_cleaned.csv", encoding="utf8") as f:
        reader = csv.reader(f, delimiter="\t")
        without_header = list(reader)[1:]
        sentences = [i[0] for i in without_header]
    return sentences[random.randint(0, len(sentences) - 1)]


def tempfile_exists():
    return os.path.isfile(os.path.join("projects", "TEMP", "tempfile.wav"))


def save_current_audio(project: Project, current_sentence: str):
    project.add_audio(current_sentence)
    shutil.move(os.path.join("projects", "TEMP", "tempfile.wav"),
                os.path.join("projects", "TEMP", "wavs", str(project.current_audio_index()) + ".wav"))


def get_new_sentence():
    return sentences[random.randint(0, len(sentences) - 1)]


def remove_temp_folder():
    if os.path.isdir(os.path.join("projects", "TEMP")):
        shutil.rmtree(os.path.join("projects", "TEMP"))


def export_project_to_zip(project: Project):
    shutil.make_archive(project.directory, 'zip', project.directory)
    return project.directory + ".zip"

# if __name__ == "__main__":
#     print(check_project_name(sys.argv[1]))
