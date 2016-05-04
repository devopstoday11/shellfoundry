import click
from cookiecutter.main import cookiecutter
from qpm.packaging.drivers_packager import DriversPackager
from qpm.packaging.shell_installer import ShellInstaller
from qpm.packaging.shell_packager import ShellPackager


@click.group()
def cli():
    pass


@cli.command()
@click.argument(u'template')
def create(template):
    """
    Create a CloudShell shell based on a template
    :param template: CloudShell shell template to be used.
    :return:
    """
    cookiecutter(template)


@cli.command()
@click.argument(u'package')
def pack(package):
    """
    Packs a CloudShell package
    :param package:
    :return:
    """
    drivers_packager = DriversPackager()
    drivers_packager.package_drivers(package)
    packager = ShellPackager()
    packager.create_shell_package(package)


@cli.command()
@click.argument(u'package')
def install(package):
    """
    Installs a CloudShell package into CloudShell
    :param package:
    :return:
    """
    installer = ShellInstaller()
    installer.install(package)


if __name__ == '__main__':
    cli()


