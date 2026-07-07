ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif

PIP ?= $(PYTHON) -m pip
IMAGE_NAME     := lalalaciccio/hls-scte35-manipulator-server
CONTAINER_NAME := hls-scte35-manipulator-server

ORIGIN_BASE_URL ?= http://host.docker.internal:5000

.PHONY: build install install-dev tests clean start docker-build docker-start docker-stop docker-delete

build:
	$(PIP) install --upgrade build
	$(PYTHON) -m build

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e .

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

clean:
	rm -rf build dist *.egg-info hls_scte35_manipulator_server/*.egg-info

start:
	hls-scte35-manipulator-server \
		--origin-base-url http://127.0.0.1:5000 \
		--profile hls_scte35_manipulator_server/profiles/profile.json \
		--host 0.0.0.0 \
		--port 4999

tests:
	pytest -s ./tests --html=./tests/report.html --self-contained-html 

docker-start:
	@if docker container inspect $(CONTAINER_NAME) >/dev/null 2>&1; then \
		docker rm -f $(CONTAINER_NAME); \
	fi
	docker run -it -p 4999:4999 --name $(CONTAINER_NAME) \
		--add-host=host.docker.internal:host-gateway \
		$(IMAGE_NAME) \
		--origin-base-url $(ORIGIN_BASE_URL) \
		--profile  profiles/profile-splice-filter.json \
		--host 0.0.0.0 \
		--port 4999

docker-build:
	docker build -t ${IMAGE_NAME}:latest .
	docker image prune -f --filter label=stage=builder

docker-stop:
	docker rm -f $(CONTAINER_NAME)

docker-delete:
	docker rm -f $(CONTAINER_NAME)
	docker rmi $(IMAGE_NAME)

docker-publish:
	docker push $(IMAGE_NAME)