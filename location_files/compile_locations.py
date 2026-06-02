#!/usr/bin/env python

"""
Script that compiles are the Location files.
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

# if you want to ignore some locations, put them here.
LOCATIONS_TO_IGNORE = []
# ["strait_of_juan_de_fuca",
#                       ]


here = Path(__file__).absolute().parent

locfile_dir = here

def check_skip(path):
    """
    check if the path is in the skip list
    """
    # check for locations to ignore
    skip = False
    for pti in LOCATIONS_TO_IGNORE:
        if pti in str(path):
            skip = True
            break
    return skip


class CompileJSON():
    def run(self):
        """
        Loops through all location file dirs and compiles the JSON
        """
        file_patterns = ['*wizard.json']
        num_locations = 0
        with open(here / 'style.css', "r") as css_file:
            for pattern in file_patterns:
                file_list = [Path(dirpath) / f
                             for dirpath, _dirnames, files in os.walk(locfile_dir)
                             for f in fnmatch.filter(files, pattern)]

                for f in file_list:
                    if check_skip(f):
                        print("skipping:", f)
                        continue
                    try:
                        self.compile(f, css_file)
                        num_locations += 1
                    except OSError as err:
                        print(("Failed to find {}. Error {}"
                               .format(f, err)))

            print(f"Compiled {num_locations} location(s)")

    def compile(self, path, css):
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


if __name__ == "__main__":
    compiler = CompileJSON()
    compiler.run()
