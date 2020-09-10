DOCKER_IMAGE_TAG = "musuems-demo"

.PHONY: build
build:
	DOCKER_BUILDKIT=1 docker build . --tag $(DOCKER_IMAGE_TAG)

.PHONY: run
run: build
	docker run -p 8080:8080 $(DOCKER_IMAGE_TAG)
