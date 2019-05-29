help:
	cat cams_to_pubsubs.makefile
run:
	docker-compose -f cams_to_pubsubs.yml up -d

build: stop rm         # i dont think this makes sense here
	docker-compose -f cams_to_pubsubs.yml build

rebuild: stop rm         # i dont think this makes sense here
	docker-compose -f cams_to_pubsubs.yml build --force-rm

stop:
	docker-compose -f cams_to_pubsubs.yml stop

rm:
	docker-compose -f cams_to_pubsubs.yml rm -f    # -f means don't ask for
#                                                      #  confirmation
