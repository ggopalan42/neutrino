help:
	cat cams_to_pubsubs.makefile
run:
	docker-compose -f cams_to_pubsubs.yml up -d

build: stop rm
	docker-compose -f cams_to_pubsubs.yml build

rebuild: stop rm
	docker-compose -f cams_to_pubsubs.yml build --force-rm

stop:
	docker-compose -f cams_to_pubsubs.yml stop

rm:
	docker-compose -f cams_to_pubsubs.yml rm
