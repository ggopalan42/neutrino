help:
	cat Makefile
run:
	docker-compose -f cams_to_pubsubs.yml up
# exec:
#	docker-compose exec cam2pub bash
build: stop .FORCE
	docker-compose -f cams_to_pubsubs.yml build
rebuild: stop .FORCE
	docker-compose build --force-rm
# stop:
#	docker stop cam2pub || true; docker rm cam2pub || true;
.FORCE:

