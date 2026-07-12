# Docker Basics: Quick Reference Guide

A practical guide to essential Docker commands for building, running, and managing containers.

---



## 1. Images: Build, List, Remove

### Building Images

```bash
# Build from Dockerfile in current directory
docker build -t myimage:latest .

# Build with build arguments
docker build -t myimage:latest --build-arg PYTHON_VERSION=3.10 .

# Build and tag with multiple tags
docker build -t myimage:latest -t myimage:v1.0 .

# Build with no cache (rebuild all layers)
docker build --no-cache -t myimage:latest .

# Build from a Dockerfile with a different name
docker build -t myimage:latest -f custom.Dockerfile .

# Build and show detailed output
docker build -t myimage:latest --progress=plain .
```

### Listing Images

```bash
# List all images
docker images

# List images with full SHA256 digest
docker images --digests

# List images for a specific repository
docker images myimage

# List only image IDs
docker images -q

# List images with custom format
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Show image creation date
docker images --format "{{.Repository}}:{{.Tag}} created {{.CreatedAt}}"
```

### Inspecting Images

```bash
# View detailed image info (layers, env vars, exposed ports, etc.)
docker image inspect myimage:latest

# Extract specific field (e.g., labels)
docker image inspect myimage:latest --format '{{json .Config.Labels}}'

# View image history (layers and sizes)
docker history myimage:latest

# View how much disk space the image uses
docker image du myimage:latest
```

### Removing Images

```bash
# Remove a single image
docker rmi myimage:latest

# Remove image by ID
docker rmi abc123def456

# Remove multiple images
docker rmi myimage:v1 myimage:v2 myimage:v3

# Force remove (even if running containers use it)
docker rmi -f myimage:latest

# Remove dangling images (untagged/orphaned)
docker image prune

# Remove all unused images
docker image prune -a

# Remove images matching a pattern
docker images | grep myimage | awk '{print $3}' | xargs docker rmi
```

### Tagging and Pushing Images

```bash
# Tag an existing image
docker tag myimage:latest myrepo/myimage:latest

# Retag with new name
docker tag old_name:latest new_name:latest

# Push to Docker Hub
docker push myrepo/myimage:latest

# Pull from Docker Hub
docker pull myrepo/myimage:latest

# Tag for private registry
docker tag myimage:latest myregistry.com/myimage:latest
docker push myregistry.com/myimage:latest
```

---

## 2. Containers: Run, Start, Stop, Remove

### Running Containers

```bash
# Run container in foreground (see output immediately)
docker run -it myimage:latest

# Run in background (detached mode)
docker run -d myimage:latest

# Run with a custom name
docker run -d --name my_container myimage:latest

# Run with port mapping (host:container)
docker run -d -p 8080:80 myimage:latest
# Now: localhost:8080 routes to container port 80

# Run with multiple port mappings
docker run -d -p 8080:80 -p 443:443 myimage:latest

# Run with environment variables
docker run -d -e DB_HOST=localhost -e DB_PORT=5432 myimage:latest

# Run with volume mount (bind host directory to container)
docker run -d -v /host/path:/container/path myimage:latest

# Run with read-only volume
docker run -d -v /host/path:/container/path:ro myimage:latest

# Run with named volume (Docker-managed storage)
docker run -d -v myvolume:/data myimage:latest

# Run with resource limits
docker run -d --memory=512m --cpus=0.5 myimage:latest

# Run with GPU support (NVIDIA)
docker run -d --gpus all myimage:latest
docker run -d --gpus '"device=0"' myimage:latest  # Use GPU 0 only

# Run with custom command
docker run -d myimage:latest /bin/bash

# Run and automatically remove container when it stops
docker run --rm myimage:latest

# Run with custom working directory
docker run -d -w /app myimage:latest

# Run as specific user
docker run -d --user 1000:1000 myimage:latest

# Combine multiple options
docker run -d \
  --name my_service \
  -p 9002:9002 \
  -v /host/data:/data \
  -e ENVIRONMENT=production \
  --gpus all \
  myimage:latest
```

### Container Lifecycle

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# List only container IDs
docker ps -q

# List with custom format
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Start a stopped container
docker start my_container

# Stop a running container (graceful shutdown)
docker stop my_container

# Stop with timeout (force kill after 10 seconds)
docker stop --time 10 my_container

# Force kill a container immediately
docker kill my_container

# Restart a container
docker restart my_container

# Pause a running container (freeze processes)
docker pause my_container

# Unpause a container
docker unpause my_container

# Remove a stopped container
docker rm my_container

# Remove a running container (force)
docker rm -f my_container

# Remove multiple containers
docker rm my_container1 my_container2 my_container3

# Remove all stopped containers
docker container prune

# Remove all stopped containers created before a date
docker container prune --filter "until=24h"
```

---

## 3. Monitoring and Logs

### View Logs

```bash
# View all logs from a container
docker logs my_container

# Follow logs in real-time (like tail -f)
docker logs -f my_container

# Show last 50 lines and follow
docker logs --tail 50 -f my_container

# Show logs with timestamps
docker logs --timestamps my_container

# Show logs from the last hour
docker logs --since 1h my_container

# Show logs since specific time
docker logs --since 2026-07-02T10:00:00 my_container

# Limit to last N lines
docker logs --tail 100 my_container

# Combine options
docker logs -f --timestamps --tail 50 my_container
```

### Monitor Resource Usage

```bash
# Show real-time resource usage (CPU, memory, network, I/O)
docker stats

# Monitor specific container
docker stats my_container

# Show once and exit (no live updates)
docker stats --no-stream

# Show with custom format
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Monitor multiple containers
docker stats my_container1 my_container2
```

### Inspect Running Container

```bash
# View detailed container info
docker inspect my_container

# Extract specific field
docker inspect my_container --format '{{.State.Status}}'

# Get IP address
docker inspect my_container --format '{{.NetworkSettings.IPAddress}}'

# Get port mappings
docker inspect my_container --format '{{json .NetworkSettings.Ports}}'

# View environment variables
docker inspect my_container --format '{{json .Config.Env}}'

# Check if running
docker inspect my_container --format '{{.State.Running}}'
```

### Execute Commands in Running Container

```bash
# Run a command in the container
docker exec my_container ls -la

# Run interactive shell in container
docker exec -it my_container /bin/bash

# Run as specific user
docker exec -u 0 my_container whoami

# Run with environment variable
docker exec -e MY_VAR=value my_container printenv MY_VAR

# Run with working directory
docker exec -w /app my_container pwd
```

---

## 4. Volumes: Create and Manage

### Named Volumes

```bash
# Create a named volume
docker volume create mydata

# List all volumes
docker volume ls

# Inspect a volume
docker volume inspect mydata

# Remove a volume
docker volume rm mydata

# Remove unused volumes
docker volume prune

# Remove all volumes
docker volume prune -a

# Mount named volume in container
docker run -d -v mydata:/data myimage:latest

# Create with driver options
docker volume create --driver local \
  --opt type=tmpfs \
  --opt device=tmpfs \
  --opt o=size=100m \
  temp_vol
```

### Bind Mounts (Host Directory)

```bash
# Mount host directory (creates if doesn't exist)
docker run -d -v /host/path:/container/path myimage:latest

# Mount as read-only
docker run -d -v /host/path:/container/path:ro myimage:latest

# Mount multiple directories
docker run -d \
  -v /host/data:/data \
  -v /host/config:/etc/config:ro \
  myimage:latest

# Mount with selinux label (Linux)
docker run -d -v /host/path:/container/path:Z myimage:latest
```

### Copy Between Host and Container

```bash
# Copy file from host to running container
docker cp /host/file.txt my_container:/container/path/

# Copy file from container to host
docker cp my_container:/container/file.txt /host/path/

# Copy directory from container to host
docker cp my_container:/container/dir /host/path/

# Copy recursively
docker cp -r my_container:/app /host/backup/
```

---

## 5. Networks

### Create and Manage Networks

```bash
# Create a custom network
docker network create mynetwork

# List networks
docker network ls

# Inspect network
docker network inspect mynetwork

# Remove network
docker network rm mynetwork

# Connect container to network
docker network connect mynetwork my_container

# Disconnect container from network
docker network disconnect mynetwork my_container

# Run container on specific network
docker run -d --network mynetwork --name web myimage:latest

# Create bridge network with options
docker network create \
  --driver bridge \
  --subnet 172.20.0.0/16 \
  --gateway 172.20.0.1 \
  mynetwork
```

### Service Discovery

```bash
# Containers on same network can ping each other by name
docker run -d --network mynetwork --name service1 myimage:latest
docker run -d --network mynetwork --name service2 myimage:latest

# From service2: ping service1
docker exec service2 ping service1

# Access via network
docker exec service2 curl http://service1:8080
```

---

## 6. Cleanup and Maintenance

### Clean Up All Unused Resources

```bash
# Remove stopped containers, dangling images, unused networks/volumes
docker system prune

# Same with volumes
docker system prune -a --volumes

# Show what will be cleaned
docker system prune --dry-run

# Get disk space usage
docker system df

# Get detailed breakdown
docker system df -v
```

### Other Cleanup

```bash
# Remove containers older than 24 hours
docker container prune --filter "until=24h"

# Remove images with no tags
docker image prune

# Remove all images not used by any container
docker image prune -a

# Remove all networks not used
docker network prune

# Remove all volumes not used
docker volume prune -a
```

---

## 7. Docker Compose (Multi-container)

### Basic Compose Commands

```bash
# Start services defined in docker-compose.yml
docker-compose up

# Start in background
docker-compose up -d

# Start specific service
docker-compose up -d myservice

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop without removing containers
docker-compose stop

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f myservice

# Execute command in service
docker-compose exec myservice /bin/bash

# List running services
docker-compose ps

# Rebuild images
docker-compose build

# Rebuild without cache
docker-compose build --no-cache
```

---

## 8. Quick Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs my_container

# Run in foreground to see immediate output
docker run -it myimage:latest

# Check if port is already in use
docker ps | grep :8080

# Inspect container state
docker inspect my_container --format '{{json .State}}'
```

### Port Conflicts

```bash
# Find what's using port 8080
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep 8080

# Kill the container using it
docker stop container_name

# Or use different port
docker run -d -p 8081:80 myimage:latest
```

### Disk Space Issues

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Remove specific large images
docker images --format "{{.Repository}}:{{.Tag}}\t{{.Size}}" | sort -k2 -hr | head -10
```

### Permission Denied Errors

```bash
# Run with elevated privileges
sudo docker run -d myimage:latest

# Or add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or run as root in container
docker run -d --user root myimage:latest
```

---

## 9. Useful One-Liners

```bash
# Kill all running containers
docker kill $(docker ps -q)

# Remove all containers
docker rm $(docker ps -aq)

# Remove all images
docker rmi $(docker images -q)

# Stop all containers
docker stop $(docker ps -q)

# Show top processes in container
docker top my_container

# See differences between image and container filesystem
docker diff my_container

# Export container filesystem as tar
docker export my_container > backup.tar

# Get container IP address
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my_container

# Count running containers
docker ps -q | wc -l

# Find container by partial name
docker ps -a --filter "name=partial_name"
```

---

## 10. Best Practices

### Dockerfile Best Practices

```dockerfile
# ❌ Bad: Single large layer
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3 python3-pip git build-essential && \
    pip install numpy scipy && \
    apt-get clean

# ✅ Good: Separate concerns, smaller layers
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3 python3-pip git build-essential
RUN pip install numpy scipy
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Multi-stage build (reduces final image size)
FROM python:3.10 as builder
RUN pip install --user numpy scipy

FROM python:3.10-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
```

### Container Best Practices

```bash
# ✅ Use specific image tags, not :latest
docker run -d myimage:v1.2.3

# ✅ Set resource limits
docker run -d --memory=1g --cpus=2 myimage:latest

# ✅ Use named volumes or bind mounts with clear paths
docker run -d -v data:/data -v config:/etc/config myimage:latest

# ✅ Use health checks
docker run -d --health-cmd='curl -f http://localhost/ || exit 1' myimage:latest

# ✅ Use custom names for easy identification
docker run -d --name web-server-prod myimage:latest

# ✅ Use environment files for secrets
docker run -d --env-file secrets.env myimage:latest
```

---

## 11. Advanced: Debugging and Development Workflow

### Development Loop

```bash
# 1. Build image
docker build -t mydev:latest .

# 2. Run container with volume mount for live code changes
docker run -it --rm \
  -v $(pwd):/app \
  -w /app \
  mydev:latest \
  /bin/bash

# 3. Edit files on host, changes reflected in container
# 4. Exit container (--rm cleans it up automatically)
```

### Debug a Failed Container

```bash
# Run with interactive shell instead of command
docker run -it myimage:latest /bin/bash

# Keep container running for inspection
docker run -d myimage:latest sleep infinity

# Check what went wrong
docker logs my_container

# Inspect inside running container
docker exec -it my_container /bin/bash

# Check installed packages
docker exec my_container pip list
docker exec my_container apt list --installed
```

### Create Debug Container from Image

```bash
# Start container that won't exit
docker run -d --name debug-container myimage:latest tail -f /dev/null

# Access it
docker exec -it debug-container /bin/bash

# Check environment
docker exec debug-container env

# Check what's in a directory
docker exec debug-container ls -la /app
```

---

## Quick Reference Table

| Task | Command |
|------|---------|
| Build image | `docker build -t name:tag .` |
| Run container | `docker run -d myimage:latest` |
| Stop container | `docker stop name` |
| View logs | `docker logs -f name` |
| Monitor resources | `docker stats` |
| Execute command | `docker exec -it name /bin/bash` |
| Copy file to container | `docker cp file.txt name:/path/` |
| View all images | `docker images` |
| Remove image | `docker rmi name:tag` |
| Remove container | `docker rm name` |
| Create volume | `docker volume create name` |
| Mount volume | `docker run -v name:/path ...` |
| List networks | `docker network ls` |
| Clean up all | `docker system prune -a --volumes` |

---

## 12. Docker Daemon & Boot Management (Linux)

To ensure Docker starts automatically when your Linux system boots, configure it using `systemd`.

### Enable Docker to Start at Boot

```bash
# Start the Docker daemon immediately
sudo systemctl start docker

# Configure Docker to launch automatically on system startup
sudo systemctl enable docker

# Check if the Docker service is active and enabled
sudo systemctl status docker
```

### Manually Start Docker Daemon (Optional)

If you prefer not to use `systemd`, you can start the daemon manually for debugging:

```bash
# Runs the daemon in the foreground, logging output directly to your terminal
# Use this only for testing/troubleshooting, not for normal operation
sudo dockerd
```

### Troubleshooting Tips

```bash
# Permission issues: make sure your user is in the docker group
sudo usermod -aG docker $USER
newgrp docker

# Check logs if Docker fails to start
sudo journalctl -u docker.service
```

Following these steps ensures Docker launches automatically at startup for a seamless containerized workflow.

---

**More info:** [Docker Docs](https://docs.docker.com/)
