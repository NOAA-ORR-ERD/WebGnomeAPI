#!/bin/bash

set -e

PYTHON_VER=${PYTHON_VER:-3.13}
PYGNOME_VER=${PYGNOME_VER:-main}
LIBGOODS_VER=${LIBGOODS_VER:-main}
WEBGNOME_API_VER=${WEBGNOME_API_VER:-main}

set -x

pixi global install git git-lfs gxx make libxext-devel-cos7-aarch64 libsm-devel-cos7-aarch64 libxrender-cos7-aarch64 libglib wget chrpath bzip2 tar patchelf ca-certificates gcc awk pixi-pack
git lfs install

if [ -d "./.tempenv" ]; then
	rm -rf ./.tempenv
fi

mkdir .tempenv
cd .tempenv

pixi init && pixi add python"=${PYTHON_VER}"

pixi add --platform win-64 posix 
# pixi add --platform osx-64 clang  ## !!!!!!!!!!!! Broken when trying to compile pygnome, can't find netcdf even though it's present.
pixi add --platform linux-64 clang

echo "Cloning repositories..."

if [ -n "${CI_JOB_TOKEN:-}" ]; then
	GIT_USER="gitlab-ci-token"
	GIT_TOKEN="${CI_JOB_TOKEN}"
else
	GIT_USER="build_key"
	GIT_TOKEN="${BUILD_KEY}"
fi

git clone https://${GIT_USER}:${GIT_TOKEN}@gitlab.orr.noaa.gov/gnome/pygnome.git -b $PYGNOME_VER --depth=1
git clone https://${GIT_USER}:${GIT_TOKEN}@gitlab.orr.noaa.gov/gnome/libgoods.git -b $LIBGOODS_VER --depth=1
git clone https://${GIT_USER}:${GIT_TOKEN}@gitlab.orr.noaa.gov/gnome/webgnomeapi.git -b $WEBGNOME_API_VER --depth=1

awk '!/^#/ && NF' ./pygnome/py_gnome/conda_requirements.txt | while read -r requirement; do pixi add "$requirement"; done
awk '!/^#/ && NF' ./libgoods/conda_requirements.txt | while read -r requirement; do pixi add "$requirement"; done
awk '!/^#/ && NF' ./webgnomeapi/conda_requirements.txt | while read -r requirement; do pixi add "$requirement"; done

pixi add --pypi build pip

echo "Build the Wheels 🛞"
pixi run python -m build ./pygnome/py_gnome -o ./pygnome-dist
pixi run python -m build ./libgoods -o ./libgoods-dist
pixi run python -m build ./webgnomeapi -o ./webgnomeapi-dist

echo "Package and inject our build wheels"
pixi exec pixi-pack --create-executable --inject $(pwd)/$(find ./pygnome-dist/*.whl) \
				  --inject $(pwd)/$(find ./libgoods-dist/*.whl) \
					--inject $(pwd)/$(find ./webgnomeapi-dist/*.whl)
