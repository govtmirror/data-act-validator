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

ADD s3bucket.json /usr/local/lib/python2.7/dist-packages/dataactcore/aws/s3bucket.json
ADD dbCred.json /usr/local/lib/python2.7/dist-packages/dataactcore/credentials/dbCred.json
ADD validator_configuration.json /usr/local/lib/python2.7/dist-packages/dataactvalidator/validator_configuration.json

CMD validator -resetDB -start
    
