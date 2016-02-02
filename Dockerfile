FROM ubuntu

RUN apt-get update && apt-get install -y \
    git \
    python-pip \
    ca-certificates \
    python-dev \
    libpq-dev \
    postgresql

ADD . /data-act

WORKDIR /data-act

RUN pip install --process-dependency-links .

CMD bin/sh
    
