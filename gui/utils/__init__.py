import os


def project_exists(project_name):
    return os.path.isdir(os.path.join("projects", project_name))

def create_project(project_name):
    print("Creating project: {}".format(project_name))