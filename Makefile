# Makefile

# Define the directories containing the Dockerfiles
DOCKER_API_DIR := docker/api
DOCKER_APP_DIR := docker/app

# Define the image names
API_IMAGE_NAME := llmstack-api
APP_IMAGE_NAME := llmstack-app


# Define the build targets
.PHONY: all app client

all: app client

client: 
	@echo "Building client..."
	cd llmstack/client && npm run build && cd ../../

api:
	@echo "Building client..."
	cd llmstack/client && npm run build && cd ../../

	@echo "Building api image..."	
	docker build -t $(API_IMAGE_NAME) -f $(DOCKER_API_DIR)/Dockerfile .

api-image:
	@echo "Building api image..."
	docker build -t $(API_IMAGE_NAME) -f $(DOCKER_API_DIR)/Dockerfile .

app:
	@echo "Building app image..."
	docker build -t $(APP_IMAGE_NAME) -f $(DOCKER_APP_DIR)/Dockerfile .
