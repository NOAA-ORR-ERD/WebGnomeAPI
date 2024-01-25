ARG CI_COMMIT_BRANCH
FROM registry.orr.noaa.gov/gnome/pygnome:${CI_COMMIT_BRANCH}

RUN conda list |grep -i gnome

# Args declared before the FROM need to be redeclared, don't delete this
ARG CI_COMMIT_BRANCH
RUN set

RUN yum update -y \
    && yum install -y redis

# why is pygnome going away?
RUN conda list |grep -i gnome

RUN ls .
COPY ./ /webgnomeapi/

# why is pygnome going away?
RUN conda list |grep -i gnome

RUN conda install mamba

RUN ls webgnomeapi
RUN ls webgnomeapi/libgoods

RUN mamba install -y \
       --file webgnomeapi/conda_requirements.txt \
       --file webgnomeapi/libgoods/conda_requirements.txt 

# Is the shell still operable at this point?
RUN ls .

# why is pygnome going away?
RUN mamba list |grep -i gnome

RUN cd webgnomeapi/libgoods && pip install .
RUN cd webgnomeapi && pip install .

RUN cd webgnomeapi && python setup.py compilejson

# why is pygnome going away?
RUN mamba list |grep -i gnome

RUN mkdir /config
RUN cp /webgnomeapi/gnome-deploy/config/webgnomeapi/config.ini /config/config.ini
RUN ln -s /config/config.ini /webgnomeapi/config.ini

# why is pygnome going away?
RUN mamba list |grep -i gnome

EXPOSE 9899
VOLUME /config
VOLUME /models
WORKDIR /webgnomeapi/
ENTRYPOINT ["/webgnomeapi/docker_start.sh"]
