#!/usr/bin/env python

import glob
import os
from shutil import copy2

from travis_project import TravisProject
import travis_job_helper

input_folder = "/tmp/travis_parser/input/"
output_folder = "/tmp/travis_parser/output/"

repo_data_file = "repo-data-travis.csv"
build_log_file = "buildlog-data-travis.csv"


if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def process_project(project_folder):
    project = create_project(project_folder)
    process_jobs(project_folder)
    copy_repo_data_file(project_folder)
    copy_build_log_file(project_folder)

    return project


def create_project(project_folder):
    project_folder_name = os.path.basename(os.path.basename(project_folder))

    project_info = project_folder_name.split('@')
    project_org = str(project_info[0])
    project_name = str(project_info[1])

    return TravisProject(project_org, project_name)


def process_jobs(project_folder):
    job_list = []

    log_listing = glob.glob(project_folder + os.sep + "*.log")
    for log_file in log_listing:
        job = travis_job_helper.parse_job_log_file(log_file)
        job_list.append(job)

    return job_list


def create_dir_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def copy_repo_data_file(project_folder):
    repo_log_source_file = project_folder + os.sep + repo_data_file
    repo_log_destination_file = output_folder + os.sep + project_folder + os.sep + repo_data_file

    create_dir_if_not_exists(os.path.dirname(repo_log_destination_file))

    if os.path.isfile(repo_log_source_file):
        copy2(repo_log_source_file, repo_log_destination_file)


def copy_build_log_file(project_folder):
    build_log_source_file = project_folder + os.sep + build_log_file
    build_log_destination_file = output_folder + os.sep + project_folder + os.sep + build_log_file

    create_dir_if_not_exists(os.path.dirname(build_log_destination_file))

    if os.path.isfile(build_log_source_file):
        copy2(build_log_source_file, build_log_destination_file)


def merge_repo_data_files():
    None


def merge_build_log_files():
    None


def main():
    project_list = []
    job_list = []

    folder_list = glob.glob(input_folder + os.sep + "*")

    for f in folder_list:
        if os.path.isdir(f):
            project = process_project(f)
            job_list = process_jobs(f)
            project.assign_jobs(job_list)
            for line in project.get_as_csv():
                print(line)
            project_list.append(project)

    print(TravisProject.get_csv_header())

    merge_repo_data_files()
    merge_build_log_files()


if __name__ == '__main__':
    main()
