DOCKER_IMAGE_TAG = "yanickc/museums-demo"

.PHONY: build
build:
	DOCKER_BUILDKIT=1 docker build . --tag $(DOCKER_IMAGE_TAG)

.PHONY: push
push: build
	docker push $(DOCKER_IMAGE_TAG)

.PHONY: pull
pull:
	docker pull $(DOCKER_IMAGE_TAG)

.PHONY: run
run:
	docker run -p 8080:8080 --detach --name museums $(DOCKER_IMAGE_TAG)
	sleep 2
	open http://localhost:8080

.PHONY: stop
stop:
	docker stop museums
	docker rm museums
