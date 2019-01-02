#!/usr/bin/python
# -*- coding: utf-8 -*-

import click
import os
import shutil
import yaml
from threading import Thread, RLock

from requests.exceptions import SSLError

from shellfoundry.utilities.config_reader import Configuration, CloudShellConfigReader
from shellfoundry.utilities.repository_downloader import RepositoryDownloader
from shellfoundry.utilities.temp_dir_context import TempDirContext
from shellfoundry.utilities.template_retriever import TemplateRetriever
from shellfoundry.exceptions import VersionRequestException


class GetTemplatesCommandExecutor(object):
    def __init__(self, repository_downloader=None, template_retriever=None):
        """
        :param TemplateRetriever template_retriever:
        :param RepositoryDownloader repository_downloader:
        """

        self.cloudshell_config_reader = Configuration(CloudShellConfigReader())
        self.template_retriever = template_retriever or TemplateRetriever()
        self.repository_downloader = repository_downloader or RepositoryDownloader()

    def get_templates(self, cs_version, output_dir=None):
        """ Download all templates relevant to provided CloudShell Version
        :param str cs_version: The desired version of the CloudShell
        :param str output_dir: Output directory to download templates
        """

        online_mode = self.cloudshell_config_reader.read().online_mode.lower() == "true"
        if online_mode:
            try:
                response = self.template_retriever._get_templates_from_github()
                config = yaml.load(response)
                repos = set(template["repository"] for template in config["templates"])

                if not output_dir:
                    output_dir = os.path.curdir

                archive_name = "shellfoundry_templates_{}".format(cs_version)

                with TempDirContext(archive_name) as temp_dir:
                    templates_path = os.path.join(temp_dir, archive_name)
                    os.mkdir(templates_path)
                    archive_path = os.path.join(output_dir, "{}.zip".format(archive_name))
                    if os.path.exists(archive_path):
                        click.confirm(
                            text="Templates archive for CloudShell Version {cs_version} already exist on path {path}."
                                 "\nDo you wish to overwrite it?".format(cs_version=cs_version,
                                                                         path=archive_path),
                            abort=True)
                        os.remove(archive_path)

                    threads = []
                    lock = RLock()
                    for repo in repos:
                        template_thread = Thread(target=self.download_template,
                                                 args=(repo, cs_version, templates_path, lock))
                        threads.append(template_thread)

                    for thread in threads:
                        thread.start()

                    for thread in threads:
                        thread.join()

                    shutil.make_archive(templates_path, "zip", templates_path)
                    shutil.move("{}.zip".format(templates_path), output_dir)

                templates_archive = "{}.zip".format(os.path.join(output_dir, templates_path))
                click.echo(
                    "Downloaded templates for CloudShell {cs_version} to {templates}".format(cs_version=cs_version,
                                                                                             templates=templates_archive))
            except SSLError:
                raise click.UsageError("Could not retrieve the templates list to download. Are you offline?")
        else:
            click.echo("Please, move shellfoundry to online mode. See, shellfoundry config command")

    def download_template(self, repository, cs_version, templates_path, lock):
        result_branch = self.template_retriever.get_latest_template(repository, cs_version)
        if result_branch:
            try:
                lock.acquire()
                self.repository_downloader.download_template(target_dir=templates_path,
                                                             repo_address=repository,
                                                             branch=result_branch,
                                                             is_need_construct=True)
            except VersionRequestException:
                click.secho("Failed to download template from repository {} version {}".format(repository,
                                                                                               result_branch),
                            fg="red")
            finally:
                lock.release()
