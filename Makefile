# IoT Service
IOT_IMAGE_NAME ?= fit4110/iot-ingestion:lab04
IOT_CONTAINER_NAME ?= fit4110-iot-lab04
IOT_PORT ?= 8000

# Analytics Service
ANALYTICS_IMAGE_NAME ?= fit4110/analytics:lab04
ANALYTICS_CONTAINER_NAME ?= fit4110-analytics-lab04
ANALYTICS_PORT ?= 8001

install:
	npm install

lint:
	npm run lint:openapi

# IoT Service Commands
mock:iot:
	npm run mock:iot

test-mock:iot:
	npm run test:mock:iot

build:iot:
	docker build -f Dockerfile -t $(IOT_IMAGE_NAME) .

run:iot:
	docker run --rm --name $(IOT_CONTAINER_NAME) -p $(IOT_PORT):8000 --env-file .env.example $(IOT_IMAGE_NAME)

run-detached:iot:
	docker run -d --rm --name $(IOT_CONTAINER_NAME) -p $(IOT_PORT):8000 --env-file .env.example $(IOT_IMAGE_NAME)

health:iot:
	curl http://localhost:$(IOT_PORT)/health

test-docker:iot:
	npm run test:local:iot

stop:iot:
	docker stop $(IOT_CONTAINER_NAME) || true

# Analytics Service Commands
mock:analytics:
	npm run mock:analytics

build:analytics:
	docker build -f Dockerfile.analytics -t $(ANALYTICS_IMAGE_NAME) .

run:analytics:
	docker run --rm --name $(ANALYTICS_CONTAINER_NAME) -p $(ANALYTICS_PORT):8001 --env-file .env.analytics.example $(ANALYTICS_IMAGE_NAME)

run-detached:analytics:
	docker run -d --rm --name $(ANALYTICS_CONTAINER_NAME) -p $(ANALYTICS_PORT):8001 --env-file .env.analytics.example $(ANALYTICS_IMAGE_NAME)

health:analytics:
	curl http://localhost:$(ANALYTICS_PORT)/api/v1/health

test-docker:analytics:
	npm run test:local:analytics

stop:analytics:
	docker stop $(ANALYTICS_CONTAINER_NAME) || true

# Combined Commands
build-all:
	$(MAKE) build:iot
	$(MAKE) build:analytics

run-all:
	$(MAKE) run-detached:iot
	$(MAKE) run-detached:analytics

stop-all:
	$(MAKE) stop:iot
	$(MAKE) stop:analytics

test-all:
	$(MAKE) test-docker:iot
	$(MAKE) test-docker:analytics

clean-reports:
	rm -f reports/*.xml reports/*.html reports/*.json
