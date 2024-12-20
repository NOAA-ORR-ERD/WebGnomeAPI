#!/usr/bin/env python

"""
    Setup file.
"""
import os
import glob
import shutil
from pathlib import Path
import fnmatch
import htmlmin
from jsmin import jsmin
import ujson
import json

from setuptools import setup, find_packages
from distutils.command.clean import clean
from distutils.command.build_py import build_py as _build_py
from setuptools.command.develop import develop
from setuptools.command.install import install

from git import Repo

# could run setup from anywhere
here = Path(__file__).absolute().parent

repo = Repo('.')
try:
    branch_name = repo.active_branch.name
except TypeError:
    branch_name = 'no-branch'

last_update = repo.iter_commits().__next__().committed_datetime.isoformat(),

with open(here / 'README.rst', encoding='utf-8') as f:
    README = f.read()


class cleanall(clean):
    description = 'cleans files generated by develop mode'

    def run(self):
        # call base class clean
        clean.run(self)

        self.clean_compiled_python_files()
        self.clean_compiled_location_files()

        rm_dir = ['pyGnome.egg-info', 'build']
        for dir_ in rm_dir:
            print("Deleting auto-generated directory: {0}".format(dir_))
            try:
                shutil.rmtree(dir_)
            except OSError as err:
                if err.errno != 2:  # ignore the not-found error
                    raise

    def clean_compiled_python_files(self):
        # clean any byte-compiled python files
        paths = [here / 'webgnome_api',
                 here / 'location_files']
        exts = ['*.pyc']

        self.clean_files(paths, exts)

    def clean_compiled_location_files(self):
        # clean any byte-compiled python files
        paths = [here / 'location_files']
        exts = ['compiled.json']

        self.clean_files(paths, exts)

    def clean_files(self, paths, exts):
        for path in paths:
            for ext in exts:
                for f in path.rglob(ext):
                    self.delete_file(f)

    def delete_file(self, filepath):
        print("Deleting auto-generated file: {0}".format(filepath))
        try:
            if filepath.is_dir():
                shutil.rmtree(filepath)
            else:
                os.remove(filepath)
        except OSError as err:
            print(("Failed to remove {0}. Error: {1}"
                  .format(filepath, err)))


class compileJSON(_build_py):
    def run(self):
        paths = [here / 'location_files']
        file_patterns = ['*wizard.json']

        with open(here / 'location_files/style.css', "r") as css_file:
            for path in paths:
                for pattern in file_patterns:
                    file_list = [Path(dirpath) / f
                                 for dirpath, _dirnames, files in os.walk(path)
                                 for f in fnmatch.filter(files, pattern)]

                    for f in file_list:
                        try:
                            self.parse(f, css_file)
                        except OSError as err:
                            print(("Failed to find {}. Error {}"
                                   .format(f, err)))

            print(("Compiled {0} location(s)".format(len(file_list))))

    def parse(self, path, css):
        if not hasattr(self, 'paths'):
            self.paths = set()

        with open(path, "r") as wizard_json:
            data = wizard_json.read()
            data_obj = ujson.loads(data)

            print(('Compiling location wizard "{}"'.format(data_obj["name"])))

            for step in data_obj["steps"]:
                dirpath = path.parent
                if dirpath not in self.paths:
                    if step["type"] == "custom":
                        self.fill_html_body(data_obj, dirpath, css)
                        self.fill_js_functions(data_obj, dirpath)
                        self.paths.add(dirpath)
                    else:
                        self.write_compiled_json(data_obj, dirpath)

    def fill_js_functions(self, obj, path):
        steps = obj["steps"]

        for file_path in path.rglob("*.js"):
            # name of the folder 2 levels above our .js file
            filename = file_path.parts[-3]

            js_file_name = file_path.stem

            for step in steps:
                if step["type"] == "custom" and step["name"] == filename:
                    print(f"    Processing {file_path}")
                    step["functions"][js_file_name] = self.jsMinify(file_path)

        self.write_compiled_json(obj, path)

    def fill_html_body(self, obj, path, css):
        steps = obj["steps"]
        for file_path in path.rglob("*.html"):
            for step in steps:
                if step["type"] == "custom" and step["name"] == file_path.stem:
                    print(f"    Processing {file_path}")
                    step["body"] = self.htmlMinify(file_path, css)
        self.write_compiled_json(obj, path)

    def htmlMinify(self, path, css):
        with open(path, "r", encoding='utf-8') as myfile:
            css.seek(0)

            css_content = css.read()
            html_content = myfile.read()

            data = "<style>" + css_content + "</style>" + html_content

            return htmlmin.minify(data)

    def jsMinify(self, path):
        with open(path, "r", encoding='utf-8') as myfile:
            return jsmin(myfile.read())

    def write_compiled_json(self, obj, path):
        with open(path / "compiled.json", 'w+') as f:
            json.dump(obj, f, indent=4)


class DevelopAll(develop, compileJSON):
    description = ('Installs some additional things that the canned command '
                   'does not')

    def run(self):
        if not self.uninstall:
            compileJSON.run(self)

        develop.run(self)


class InstallAll(install, compileJSON):
    description = ('Installs some additional things that the canned command '
                   'does not')

    def run(self):
        compileJSON.run(self)
        install.run(self)


def get_version(pkg_name):
    """
    Reads the version string from the package __init__ and returns it
    """
    with open(Path(pkg_name) / "__init__.py",
              encoding="utf-8") as init_file:
        for line in init_file:
            parts = line.strip().partition("=")
            if parts[0].strip() == "__version__":
                return parts[2].strip().strip("'").strip('"')
    return None


setup(name='webgnome_api',
      version=get_version('webgnome_api'),
      description=('webgnome_api'
                   'Branch: {}'
                   'LastUpdate: {}'
                   .format(branch_name, last_update)),
      long_description=README,
      classifiers=["Programming Language :: Python",
                   "Framework :: Pylons",
                   "Topic :: Internet :: WWW/HTTP",
                   "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
                   ],
      keywords="adios gnome oilspill weathering trajectory modeling",
      author='ADIOS/GNOME team at NOAA ORR',
      author_email='orr.gnome@noaa.gov',
      url='',
      cmdclass={'cleanall': cleanall,
                'develop': DevelopAll,
                'install': InstallAll,
                'compilejson': compileJSON
                },
      packages=find_packages(),
      include_package_data=True,
      package_data={#"webgnome_api": ["*.txt", "*.yaml"],
                    "webgnome_api.views": ["deployed_environment.yaml"],
                    },
      zip_safe=False,
      test_suite='webgnome_api',
      entry_points=('[paste.app_factory]\n'
                    '  main = webgnome_api:main\n'
                    '[paste.server_factory]\n'
                    '  srv = webgnome_api:server_factory\n'),
      )
