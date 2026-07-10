---
description: "Execute the Docker tutorial (further_materials/01_docker_tutorial) step by step — verify Docker commands, image builds, container lifecycle, labels, ports, and layers."
agent: "agent"
tools: [execute, read, search]
---

Walk through every executable step in the Docker tutorial at `further_materials/01_docker_tutorial/Readme.md`. Each section has specific commands to run. Execute them and verify the expected output.

## A First Overview

### Step 1: Check Docker version
```bash
docker --version
```
Must print a version string.

### Step 2: Run your first container
```bash
docker run hello-world
```
Must print the "Hello from Docker!" message.

### Step 3: List images
```bash
docker images
```
Must list at least the hello-world image.

### Step 4: List running containers
```bash
docker ps
```
Should be empty (hello-world already exited).

### Step 5: List all containers
```bash
docker ps -a
```
Must show the stopped hello-world container.

### Step 6: Arguments to programs
```bash
docker pull busybox
docker run busybox ls
```

### Exercise: Alpine echo
```bash
docker run alpine echo "Hello from Alpine"
```

## Running Containers

### Step 1: Interactive container
```bash
docker run --rm alpine echo "interactive test passed"
```

### Step 2: Detached mode
```bash
docker run -d --name tutorial-sleep alpine sleep 10
docker logs tutorial-sleep
```

### Step 3: Stop container
```bash
docker stop tutorial-sleep
```

### Step 4: Remove container
```bash
docker rm tutorial-sleep
```

## Building Images

### Step 1–3: Build and run a custom image
Create a temporary directory, write a Dockerfile, build and run:

```bash
TUTORIAL_DIR=$(mktemp -d)
cat > "$TUTORIAL_DIR/Dockerfile" <<'EOF'
FROM alpine:3.22.1
RUN apk add figlet
CMD ["figlet", "Hello from Alpine!"]
EOF
docker build -t tutorial-figlet "$TUTORIAL_DIR"
docker run --rm tutorial-figlet
rm -rf "$TUTORIAL_DIR"
```

Must print ASCII art "Hello from Alpine!".

## Labels and Metadata

### Step 1: Labels in Dockerfile
```bash
TUTORIAL_DIR=$(mktemp -d)
cat > "$TUTORIAL_DIR/Dockerfile" <<'EOF'
FROM alpine:3.22.1
LABEL maintainer="test@example.com"
LABEL version="1.0"
LABEL description="Demo image with labels"
CMD ["echo", "Labels are cool!"]
EOF
docker build -t tutorial-labeled "$TUTORIAL_DIR"
docker inspect --format='{{json .Config.Labels}}' tutorial-labeled
docker inspect --format='{{index .Config.Labels "version"}}' tutorial-labeled
rm -rf "$TUTORIAL_DIR"
```

Must show the labels including `version: 1.0`.

### Step 2: Labels from CLI
```bash
TUTORIAL_DIR=$(mktemp -d)
cat > "$TUTORIAL_DIR/Dockerfile" <<'EOF'
FROM alpine:3.22.1
CMD ["echo", "cli label test"]
EOF
docker build --label project=demo -t tutorial-cli-label "$TUTORIAL_DIR"
docker inspect --format='{{index .Config.Labels "project"}}' tutorial-cli-label
rm -rf "$TUTORIAL_DIR"
```

Must output `demo`.

## Exposing Ports

### Step 1: Run nginx with exposed port
```bash
docker run -d --name tutorial-nginx -p 18080:80 nginx:alpine
sleep 2
curl -s http://localhost:18080 | head -5
docker stop tutorial-nginx && docker rm tutorial-nginx
```

Must return HTML from nginx.

## Image Layers and Tags

```bash
docker image history alpine:3.22.1
```

## Cleanup

Remove tutorial images and containers:
```bash
docker rmi tutorial-figlet tutorial-labeled tutorial-cli-label 2>/dev/null || true
docker container prune -f
```

## Report

Summarize which steps passed and which failed. Note any Docker daemon issues or network problems.
