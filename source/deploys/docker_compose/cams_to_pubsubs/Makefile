help:
	cat Makefile
run:
	docker-compose up -d

build: stop rm         # i dont think this makes sense here
	docker-compose build

rebuild: stop rm         # i dont think this makes sense here
	docker-compose build --force-rm

stop:
	docker-compose stop

rm:
	docker-compose rm -f    # -f means don't ask for
#                               #  confirmation
