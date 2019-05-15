#!/usr/bin/env python


class TravisProject:
    """
    Data storage for one TravisTorrent project
    """

    def __init__(self, project_org, project_name, jobs = []):
        self.__project_org = project_org
        self.__project_name = project_name
        self.__jobs = jobs

    @property
    def project_org(self):
        return self.__project_org

    @property
    def project_name(self):
        return self.__project_name

    def assign_jobs(self, job_list):
        self.__jobs = job_list
