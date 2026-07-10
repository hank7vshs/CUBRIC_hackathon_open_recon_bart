- [Getting Started with Docker](#getting-started-with-docker)
  - [A first overview](#a-first-overview)
    - [Step 1: Check Docker version](#step-1-check-docker-version)
    - [Step 2: Run your first container](#step-2-run-your-first-container)
    - [Step 3: List images](#step-3-list-images)
    - [Step 4: List running containers](#step-4-list-running-containers)
    - [Step 5: List all containers (including stopped ones)](#step-5-list-all-containers-including-stopped-ones)
    - [Step 6: Arguments to the program in a container](#step-6-arguments-to-the-program-in-a-container)
    - [Exercise](#exercise)
  - [Running Containers](#running-containers)
    - [Step 1: Run an interactive container](#step-1-run-an-interactive-container)
    - [Step 2: Detached mode](#step-2-detached-mode)
    - [Step 3: Stopping a container](#step-3-stopping-a-container)
    - [Step 4: Removing containers](#step-4-removing-containers)
    - [Exercise](#exercise-1)
  - [Building Images](#building-images)
    - [Step 1: Write a simple Dockerfile](#step-1-write-a-simple-dockerfile)
    - [Step 2: Build the image](#step-2-build-the-image)
    - [Step 3: Run the image](#step-3-run-the-image)
    - [Exercise](#exercise-2)
  - [Dockerfile Basics](#dockerfile-basics)
    - [Key instructions](#key-instructions)
    - [Exercise](#exercise-3)
  - [Labels and Metadata](#labels-and-metadata)
    - [Step 1: Labels in Dockerfile](#step-1-labels-in-dockerfile)
    - [Step 2: Labels from the CLI](#step-2-labels-from-the-cli)
  - [Exercise](#exercise-4)
  - [Exposing Ports](#exposing-ports)
    - [Step 1: Run a container exposing a port](#step-1-run-a-container-exposing-a-port)
    - [Step 2: Dockerfile EXPOSE instruction](#step-2-dockerfile-expose-instruction)
    - [EXPOSE vs -p in Docker](#expose-vs--p-in-docker)
    - [Exercise](#exercise-5)
  - [Image Layers and Tags](#image-layers-and-tags)
  - [Exercise](#exercise-6)
- [Summary and Cleanup](#summary-and-cleanup)
  - [What you learned](#what-you-learned)
  - [Cleanup](#cleanup)


# Getting Started with Docker

This part of the tutorial will familiarize you with Docker.

## A first overview

Open Recon packages MRI reconstruction software as Docker containers. You can view those as a virtual machine with an operating system based on Linux.

This section of the tutorial teaches you about Docker and verifies its functionality in your development environment.

---

### Step 1: Check Docker version

The Docker software itself consists of a runtime allowing to run *containers* and a command-line tool allowing to manage *images and containers*. 
An *image* is the static data which will be given to the runtime to create a running instance which is then called a *container*.
Most of the exercises will be done in a terminal. To open one in this devcontainer, select `Terminal` → `New Terminal` from the menu bar.
First check your version of the Docker software:

```bash
docker --version
```
### Step 2: Run your first container

Now, we do a deep dive by running our first container:

```bash
docker run hello-world
```

This downloads a small image, creates a container from that image, and runs a program in that container which prints a message.

### Step 3: List images

Since the previous command downloaded an image let us see what images are already stored locally by Docker:

```bash
docker images
```

This should at least list the hello-world image and possibly more.

### Step 4: List running containers

An important distinction with Docker is between an image and a container. A container is a live instantiation of an image. An image is data which is used to create a container.
Images can be used multiple times to create different containers. Once a container is created, it is independent of the image — changes to the image do not affect existing containers, and changes inside a running container do not affect the image.
Also, because they have a lifecycle, containers can be started and stopped, which an image cannot.
To display existing, running containers:

```bash
docker ps
```

This will come back empty because the hello-world image was used to create a container, the container ran its program and stopped after the program has terminated.

### Step 5: List all containers (including stopped ones)

To list stopped containers use:

```bash
docker ps -a
```

This will now also list the terminated hello-world container.

### Step 6: Arguments to the program in a container

When the hello-world image is run it is configured to run a program called hello-world. Some images do not have a program configured to automatically run. 
Let's manually download a new image which we want to run called *busybox*. The *pull* command explicitly asks Docker to download an image:

```bash
docker pull busybox
```

Now run this new image:

```bash
docker run busybox
```

The container will produce no output since no program is run. Run

```bash
docker run --help 
```

This will produce an output telling you that "run" actually also accepts options and a *command* after the image name followed by *arguments* for that command. Let's use the "ls" program as command:

```bash
docker run busybox ls
```

> **How this repository uses it:** The Dockerfile in `server/Dockerfile` defines a default `CMD` that starts the Python server. The script `server/run_docker.sh` passes the module name (e.g. `r2ci_bart`) as an environment variable (`-e OR_MODULE=...`), which the `CMD` reads to select the reconstruction module at startup. This is the same interplay between `CMD`, `ENV`, and runtime arguments you practice here.

### Exercise

Now that you are familiar with the crucial elements of Docker, let's do a self-directed exercise.
For this we will use a special Docker image with a very small Linux distribution called [Alpine](https://hub.docker.com/_/alpine).
Use this image to run a container which you instruct to use the `echo` program to say something like "Hello from Alpine". `echo` is a program which takes a single argument and writes this argument into the terminal. If you are unfamiliar with it, type `echo hello` in your terminal.
Inspect the images you downloaded and the containers you ran.

## Running Containers

Learn how to start, interact with, and stop containers.

---

### Step 1: Run an interactive container

Sometimes just running a single command in a container is tedious and one would like to be able to run programs from a shell inside the container. This can be achieved with the `-it` flags:

```bash
docker run -it alpine sh
```

Here `-i` keeps standard input open (so you can type commands) and `-t` allocates a terminal (so the output is formatted nicely). Together they give you an interactive shell session inside the container.

```bash
ls
```

Exit with:

```bash
exit
```

### Step 2: Detached mode

Another use case is containers which should run in the background to deliver a service. This can be achieved with the `-d` option:

```bash
docker run -d alpine sleep 60
```
This runs an Alpine container in the background.

To see the output of a detached container, use `docker logs`:
```bash
docker logs <container_id>
```

### Step 3: Stopping a container

While this Alpine container is still running we may want to stop it. We can do this by first finding out its container id and explicitly asking it to stop:

```bash
# Find ID of docker container
docker ps

# Stop running docker container
docker stop <container_id>
```

### Step 4: Removing containers

A stopped container is not deleted. This is important as during its runtime it may have modified files inside the container e.g. saving data. This information is only fully removed if the container is deleted:

```bash
# Delete docker container
docker rm <container_id>
```

> **How this repository uses it:** `server/run_docker.sh` does exactly this before each run — it calls `docker stop` and `docker rm` on any existing container named `open_recon_server` so the new container can bind port 9002 without conflicts.

### Exercise

1. Run an Alpine container interactively.
2. Install figlet inside it by executing: `apk add figlet`
3. Pass `Docker !` as argument to figlet.

## Building Images

So far we have exclusively used existing Docker images and created containers from them. For Open Recon applications we will need to create our own images. The following section will teach you how to do this.

---

### Step 1: Write a simple Dockerfile
You can do this exercise in any folder in this devcontainer, but we recommend creating a new folder for it (e.g. `exercise/`).

Create a file named "Dockerfile" with the following content:

```dockerfile
FROM alpine:3.22.1
RUN apk add figlet
CMD ["figlet", "Hello from Alpine!"]
```

The `FROM` instruction tells Docker which base image to build upon. It is good practice for reproducible images to supply an exact version tag.

> **How this repository uses it:** `server/Dockerfile` uses `FROM python:3.12-slim-bullseye` — a Debian-based Python image pinned to an exact version for reproducibility on the scanner.

The `RUN` instruction executes a shell command **during the image build** — it runs once when creating the image and does not run again when you start a container. `CMD` is the opposite: it is **not** executed during the build. Instead, it defines the default command that runs when a container starts (unless you override it on the command line).

### Step 2: Build the image

Now navigate to your exercise folder and build your first own Docker image using the file you just created:

```bash
docker build -t my-first-image .
```

The `-t` option assigns a *tag* (name) to your image — in this case `my-first-image`. You can verify the result with `docker images`. The `.` at the end tells Docker to use the current folder as the *build context* and to look for a file called `Dockerfile` there. If you want to use a different filename, use the `-f` option followed by the path to your Dockerfile.

### Step 3: Run the image

Now that you created your first image, you can run it just like the previous images:

```bash
docker run my-first-image
```

### Exercise
Edit the Dockerfile so that figlet prints a different message.
Rebuild and run the image.

## Dockerfile Basics

Now that we have learned how to write a basic Dockerfile, let us look at the full set of commonly used instructions.

---

### Key instructions
- **FROM**: Base image
- **RUN**: Execute command during build
- **COPY / ADD**: Add files into image
- **WORKDIR**: Set working directory
- **CMD**: Default command when container runs
- **ENTRYPOINT**: Define entry point for container
- **ENV**: Set environment variable
- **LABEL**: Attach metadata to the image

> **How this repository uses it:** `server/Dockerfile` uses nearly all of these instructions: `FROM` for the base image, `RUN` to install system packages and compile BART, `COPY` to add the server code, `WORKDIR` to set the build directory, `ENV` for paths like `BART_TOOLBOX_PATH` and the module selector `OR_MODULE`, `LABEL` for the application specification, and `CMD` to start the server. Open the file and see how many you can spot.

---

### Exercise  
Write a Dockerfile that:
1. Starts from `python:3.12-alpine`.
2. Sets the working directory to `/app`.
3. Copies a file `hello.py` into the container (the file can simply use `print()` to output some text).
4. Runs it with `python hello.py`. *Hint: Think about the difference between `RUN` and `CMD`.*

Then build your image and run a container from it.

## Labels and Metadata

Understand how to attach metadata to Docker images and containers.

---

### Step 1: Labels in Dockerfile
Create this Dockerfile:
```dockerfile
FROM alpine:3.22.1
LABEL maintainer="you@example.com"
LABEL version="1.0"
LABEL description="Demo image with labels"
CMD ["echo", "Labels are cool!"]
```

We can now build this image (assuming you named the file `Dockerfile` and put it into its own folder):

```bash
docker build -t labeled-image .
```
After building this image we can now inspect it:

```bash
docker inspect --format='{{json .Config.Labels}}' labeled-image
```

This will return a list of all labels which were applied to the image.
We can also look for a specific label:

```bash
docker inspect --format='{{index .Config.Labels "version"}}' labeled-image
```

### Step 2: Labels from the CLI
You can also add labels at build time:
```bash
docker build --label project=demo -t other-labeled-image .
```
Inspect the new image:
```bash
docker inspect --format='{{index .Config.Labels "project"}}' other-labeled-image
```

## Exercise
Create an image with labels for:
- Your name
- Today’s date
- A description of the project
> **Open Recon** requires every application to embed its `appl_spec.json` as a Docker label — this is how the scanner reads the application specification without having to start the container.
>
> **How this repository uses it:** `server/docker_build.sh` base64-encodes the JSON and passes it via `--label` during the build.
## Exposing Ports

Since they are like virtual machines, Docker containers are isolated computers by default. A typical way for them to communicate is over network interfaces. In order to communicate from a different machine to the Docker container, we need the operating system and the Docker runtime to allow communication over network ports.

---

### Step 1: Run a container exposing a port

To expose a port from inside the container we need to map it to a corresponding port of the host machine:
```bash
docker run -d -p 8080:80 nginx:alpine
```
The `-p` option here maps port `8080` of the host machine to port `80` inside the container. The `nginx` image contains a popular webserver that listens on port 80 by default.

Now query this port. You can use `curl` from the command line — it sends an HTTP request and prints the server's response:

```bash
curl http://localhost:8080
```

### Step 2: Dockerfile EXPOSE instruction

Dockerfiles also have a special instruction `EXPOSE` to document which port the application uses:
```dockerfile
FROM nginx:alpine
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build with:
```bash
docker build -t my-nginx .
```

Run with:
```bash
docker run -d -p 8081:80 my-nginx
```

### EXPOSE vs -p in Docker

- **EXPOSE (in Dockerfile)**  
  - Declares which ports the application *inside the container* listens on.  
  - Acts as **documentation / metadata**.  
  - Does **not** make the port accessible on the host.  

- **-p (on the command line)**  
  - Publishes a container port to the host: `-p <host_port>:<container_port>`.  
  - This is what **actually** makes the port accessible from outside the container.  
  - Works regardless of whether `EXPOSE` was used in the Dockerfile.  

In short: `EXPOSE` documents intent; `-p` enables access.

> **Open Recon** communicates with reconstruction containers over TCP on port **9002** — this is defined in the `appl_spec.json` and is the port the scanner sends data to.
>
> **How this repository uses it:** `server/run_docker.sh` maps this port with `-p 9002:9002` so the test client can reach the server inside the container.

### Exercise
So far we used the nginx webserver. In this exercise we build our own webserver application based on Python's `http.server` module.

1. Run `python -m http.server` in your terminal to see the Python webserver start.
2. Create a Dockerfile which starts from `python:3.12-alpine`.
3. Make the Python webserver start in that Dockerfile in a directory of your choice.
4. Create a new file which ends in `.html` and contains:

```html
<!DOCTYPE html>
<html>
    <head>
        <title>Example</title>
    </head>
    <body>
        <p>This is an example of a simple HTML page with one paragraph.</p>
    </body>
</html>
```

5. Copy this file to the same directory where your webserver starts.
6. State which port is used in the metadata.
7. Build and run the application.
8. Query port 8000 over your browser or using curl.
9. Query your website as `localhost:8000/<filename>`.

## Image Layers and Tags

Many Docker images use the same base images. Consider how often we used the Alpine image in this tutorial. This offers the opportunity to save disk space by reusing commonly used parts of images. Docker does this automatically using *layers*.
A layer is created for each `RUN`, `COPY`, or `ADD` instruction in the Dockerfile. Common layers between two images are only stored once. Consider a large base image containing CUDA and a whole inference engine for Deep Learning. Such an image can grow very large. Using layers, the disk space is only used once despite potentially many applications being built on top.

A practical example can be seen when pulling a specific Alpine image:
```bash
docker pull alpine:3.22.1
```
If the layers for this version are already present locally (e.g. because `alpine:latest` currently points to the same release), Docker will not download anything.

*Tags* are human-readable names for specific versions of an image. In `alpine:3.22.1`, the tag is `3.22.1`. The special tag `latest` is the default when no tag is specified — `docker run alpine` is equivalent to `docker run alpine:latest`. Always use an explicit version tag in Dockerfiles for reproducibility.

We can inspect the layers of an image using:

```bash
docker image history alpine:3.22.1
```

> **How this repository uses it:** `server/Dockerfile` is deliberately ordered so that layers change as rarely as possible. System packages and BART compilation (slow, rarely changed) come first; the application code (`COPY . ...`) comes last. This way, rebuilding after a code change only recreates the final layer instead of recompiling everything from scratch.

## Exercise

Inspect the history of your own custom images.

# Summary and Cleanup

With this tutorial, you have all the necessary knowledge to containerize an application to be able to package it for Open Recon. Continue with the [main tutorial](../../Readme.md) to build and deploy a full reconstruction pipeline.

## What you learned
- How to run containers
- How to build images
- Dockerfile basics (FROM, RUN, CMD, COPY, WORKDIR, ENV, LABEL, EXPOSE)
- Labels as metadata
- How to expose ports to access services
- Image layers and tags

---

## Cleanup
Remove all stopped containers:
```bash
docker container prune
```

Remove all images which are untagged:
```bash
docker image prune
```