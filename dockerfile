ARG CI_COMMIT_BRANCH
FROM registry.orr.noaa.gov/gnome/pygnome:${CI_COMMIT_BRANCH}

RUN conda list pygnome

# Args declared before the FROM need to be redeclared, don't delete this
ARG CI_COMMIT_BRANCH
RUN set

RUN yum update -y \
    && yum install -y redis

RUN ls .
COPY ./ /webgnomeapi/

RUN ls webgnomeapi
RUN ls webgnomeapi/libgoods

# why is pygnome going away?
RUN conda list pygnome

RUN conda install -y \
       --file webgnomeapi/conda_requirements.txt \
       --file webgnomeapi/libgoods/conda_requirements.txt 

# why is pygnome going away?
RUN conda list pygnome

# regardless why, pygnome is gone at this point.  Reinstall. 
RUN cd pygnome/py_gnome && pip install .

RUN cd webgnomeapi/libgoods && pip install .
RUN cd webgnomeapi && pip install .

RUN cd webgnomeapi && python setup.py compilejson

RUN mkdir /config
RUN cp /webgnomeapi/gnome-deploy/config/webgnomeapi/config.ini /config/config.ini
RUN ln -s /config/config.ini /webgnomeapi/config.ini

EXPOSE 9899
VOLUME /config
VOLUME /models
WORKDIR /webgnomeapi/
ENTRYPOINT ["/webgnomeapi/docker_start.sh"]
