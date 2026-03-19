#!/usr/bin/env python

"""
Script to read a conda-stye requirements file, and write it out as toml

This will create a toml file which you cn then copy and paste into a
pixi.toml file.


ToDo:

 * Have it take multiple condaa_requirement files an combine them sensibly

 * Have it update the requirements directly in a pixi.toml file.

NOTE: conda can take the same requirement with two different versions
and try to resolve them -- not sure pixi can do that.

Darn:

 numpy  = ">=2.0,<3  # works with numpy 1 and 2"
    · ──┬──
    ·   ╰── first defined here
 17 │ scipy = "*"
.
.
.
 32 │ extract_model = "*"
 33 │ numpy = "*"
    · ──┬──
    ·   ╰── duplicate defined here

No -- it can't.

which means this code should be smart about it -- which is hard !

The current code uses a dict, so duplicates are removed.

"""
import sys

DEFAULT_PYTHON_VERSION = "3.13"

def parse_req(line):
    for i, c in enumerate(line):
        if c in {'=','<','>'}:
            ind=i
            break
    else:
        ind = i+1
    # if "numpy" in line:
    #     breakpoint()
    req = line[:ind].strip()
    version = line[ind:].split("#")
    version[0] = f'"{version[0].strip()}"' if version[0] else '"*"'
    version = "  # ".join(version)

    return req, version

def extract_reqs(conda_req_file):
    """
    Extract the requirements from a conda requirements file.
    """

    in_reqs = (line.strip() for line in open(conda_req_file, encoding="utf-8").readlines())
    in_reqs = [line for line in in_reqs if line and not line.startswith("#")]


    reqs = {}
    for line in in_reqs:
        req, version = parse_req(line)
        if req in reqs:  # this is a duplicate
            # not very smart, but will preserve a pin over unpinned
            # if there are multipel different pins, then we get
            # the first one that was defined
            version = version if reqs[req] is None else reqs[req]
        reqs[req] = version

    return reqs

def write_to_toml(reqs, toml_file):
    print("writing:", toml_file)
    with open(toml_file, "w") as outfile:
        outfile.write("[dependencies]\n")
        for req, ver in reqs.items():
            outfile.write(f"{req} = {ver}\n")


if __name__ == "__main__":
    args = sys.argv[1:]

    # look for Python version
    python_ver = DEFAULT_PYTHON_VERSION
    for arg in args:
        if "python=" in arg.lower():
            python_ver = arg.strip().split("=")[1]
        else:
            conda_req_file = arg.strip()

    toml_file = conda_req_file.removesuffix(".txt") + ".toml"

    reqs = extract_reqs(conda_req_file)
    # apply the python version
    reqs["python"] = f'"{python_ver}.*"'

    # write it out to a TOML file:

    write_to_toml(reqs, toml_file)


# with open("pixi.toml", "r") as f:
#     pixi_config = f.readlines()

# print(pixi_config)

# # find existing deps:
# for line in pixi_config:
#     if line.strip() != [dependencies]:
#         continue


# deps = {"python": "3.13"}

# # pixi_config['dependencies'] = deps
# # with open("pixi2.toml", "wb") as f:
# #     pixi_config = tomllib.dump(f, pixi_config)

