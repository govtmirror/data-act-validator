.PHONY: default run build

default: run 

build:
	docker build -t ubuntu/data-act .

run: stop-app
	docker run -p 8080:80 --name=validator -d -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY ubuntu/data-act

bootstrap: db-init run

db-start: db-clean
	docker run -d -p 5432:5432 --name=postgres postgres
	sleep 3

db-init: db-start
	docker run --rm=true --name=validator-db-reset ubuntu/data-act validator -resetDB

db-clean:
	docker stop postgres
	docker rm postgres

stop-app:
	docker stop validator
	docker rm validator

validate:	cleantests
	docker run  --name=validatortest  -it --rm --link validator:validator -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -v $$(pwd):/data-act ubuntu/data-act /bin/sh -c 'cd tests; python runTests.py'

it:
	docker run  -it --rm --link validator:validator -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -v $$(pwd):/data-act ubuntu/data-act /bin/bash

cleantests:
	rm -rf tests/test-repots
