# script / instructions for building a conda environment for webgnomeapi
# NOTE: this won't work write if run as a script -- copy and paste the commands to your command line.
#    or use "source make_conda_environment.sh"


PYTHON_VER=3.10

# start with a new environment with the version of Python that you want:
conda create -n gnome_test_$PYTHON_VER python=$PYTHON_VER

# activate it:
echo "activating gnome_test"
conda activate gnome_test
echo "echo $CONDA_DEFAULT_ENV is activated"

# conda install python=$PYTHON_VER --file ../pygnome/conda_requirements.txt
# conda install  --file ../oil_database/adios_db/conda_requirements.txt
# conda install  --file ../libgoods/conda_requirements.txt
# conda install  --file ../libgoods/model_catalogs/conda_requirements.txt
# conda install  --file conda_requirements.txt

# or, all in one command:

conda install -y python=3.9.* \
      --file ../pygnome/conda_requirements.txt \
      --file ../oil_database/adios_db/conda_requirements.txt \
      --file ../libgoods/conda_requirements.txt \
#      --file ../libgoods/model_catalogs/conda_requirements.txt \
      --file conda_requirements.txt \
      --file conda_requirements_test.txt
