#!/usr/bin/env python

from travis_job import TravisJob

class TravisProject:
    """
    Data storage for one TravisTorrent project
    """

    def __init__(self, project_org, project_name):
        self.__project_org = project_org
        self.__project_name = project_name
        self.__jobs = None

    @property
    def project_org(self):
        return self.__project_org

    @property
    def project_name(self):
        return self.__project_name

    def assign_jobs(self, job_list):
        self.__jobs = job_list

    def get_as_csv(self):
        project_csv_entries = []
        project = self.__project_org + '/' + self.__project_name
        for job_entry in self.__jobs:
            project_csv_entries.append("{},{}".format(project, job_entry.get_as_csv()))

        return project_csv_entries

    @staticmethod
    def get_csv_header():
        return "{},{}".format("project", TravisJob.get_csv_header())
