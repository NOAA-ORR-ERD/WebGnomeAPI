FROM pygnome

ARG CI_COMMIT_BRANCH
RUN set

RUN yum update -y \
    && yum install -y redis

RUN ls .
COPY ./ /webgnomeapi/

RUN conda install mamba

RUN ls webgnomeapi
RUN ls webgnomeapi/libgoods

RUN mamba install -y \
       --file webgnomeapi/conda_requirements.txt \
       --file webgnomeapi/libgoods/conda_requirements.txt 

RUN conda remove --force mc-goods

RUN cd webgnomeapi/libgoods && pip install .
RUN cd webgnomeapi/mc-goods && pip install .
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
