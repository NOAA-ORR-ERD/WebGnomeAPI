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


here = Path(__file__).absolute().parent

class CompileJSON():
    def run(self):
        paths = [here]
        file_patterns = ['*wizard.json']

        with open(here / 'style.css', "r") as css_file:
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


if __name__ == "__main__":
    compiler = CompileJSON()
    compiler.run()
