ARG CI_COMMIT_BRANCH
FROM registry.orr.noaa.gov/gnome/pygnome:${CI_COMMIT_BRANCH}

# Args declared before the FROM need to be redeclared, don't delete this
ARG CI_COMMIT_BRANCH

RUN yum update -y && yum install -y redis

COPY ./ /webgnomeapi/
WORKDIR /webgnomeapi/

RUN conda install -n base conda-libmamba-solver
RUN conda config --set solver libmamba

RUN conda install -y \
        --file conda_requirements.txt \
        --file libgoods/conda_requirements.txt 

RUN cd libgoods && pip install .
RUN pip install .

RUN python setup.py compilejson

RUN mkdir /config
RUN cp gnome-deploy/config/webgnomeapi/config.ini /config/config.ini
RUN ln -s /config/config.ini /webgnomeapi/config.ini

EXPOSE 9899
VOLUME /config
VOLUME /models
ENTRYPOINT ["/webgnomeapi/docker_start.sh"]
