ARG CI_COMMIT_BRANCH
ARG PYTHON_VER
FROM registry.orr.noaa.gov/gnome/pygnome:${CI_COMMIT_BRANCH}

# Args declared before the FROM need to be redeclared, don't delete this
ARG CI_COMMIT_BRANCH
ARG PYTHON_VER

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y redis

COPY ./ /webgnomeapi/
WORKDIR /webgnomeapi/

# Make sure we are using mamba...
# RUN conda install -n base conda-libmamba-solver
# RUN conda config --set solver libmamba

RUN conda install -y python=$PYTHON_VER \
        --file conda_requirements.txt \
        --file libgoods/conda_requirements.txt \
        --file /pygnome/py_gnome/conda_requirements.txt

RUN cd libgoods && python -m pip install ./
RUN python -m pip install ./

# RUN python setup.py compilejson

RUN mkdir /config
RUN cp gnome-deploy/config/webgnomeapi/config.ini /config/config.ini
RUN ln -s /config/config.ini /webgnomeapi/config.ini

EXPOSE 9899
VOLUME /config
VOLUME /models
ENTRYPOINT ["/webgnomeapi/docker_start.sh"]
