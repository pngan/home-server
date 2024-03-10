# Docker Compose for Home Server

The components of the Home Server running on the Mac-Mini (Ubuntu) is configured by the `docker-compose.yml` file in this repo.

The main component is an nginx reverse proxy which passes commands to a number of applications.

## To add a new application 
- Edit the `docker-compose.yml` file in this repo
- Edit `./data/nginx/app.conf`, and add new service

### To start and stop docker containers
`docker-compose up`
`docker-compose down`

### To start and stop docker service
`docker-compose stop ipmon`
`docker-compose start ipmon`

### To serve files

Copy the files into the `apps` folder. This is mapped in the `nginx` container as the `/apps` folder.


## Trouble Shooting
### When `docker-compose up` fails 

_Error_: similar to "docker.errors.DockerException: Credentials store error"

_Solution_: Edit  `~/.docker/config.json` so that `credStore:` value is empty:

{"auths":{},"credsStore":"","experimental":"disabled","stackOrchestrator":"swarm"}



# Original README.md from `https://github.com/wmnnd/nginx-certbot`
# Boilerplate for nginx with Let’s Encrypt on docker-compose

> This repository is accompanied by a [step-by-step guide on how to
set up nginx and Let’s Encrypt with Docker](https://medium.com/@pentacent/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71).

`init-letsencrypt.sh` fetches and ensures the renewal of a Let’s
Encrypt certificate for one or multiple domains in a docker-compose
setup with nginx.
This is useful when you need to set up nginx as a reverse proxy for an
application.

## Installation
1. [Install docker-compose](https://docs.docker.com/compose/install/#install-compose).

2. Clone this repository: `git clone https://github.com/wmnnd/nginx-certbot.git .`

3. Modify configuration:
- Add domains and email addresses to init-letsencrypt.sh
- Replace all occurrences of ngan.familyds.com with primary domain (the first one you added to init-letsencrypt.sh) in data/nginx/app.conf

4. Run the init script:

        ./init-letsencrypt.sh

5. Run the server:

        docker-compose up

## Got questions?
Feel free to post questions in the comment section of the [accompanying guide](https://medium.com/@pentacent/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71)

## License
All code in this repository is licensed under the terms of the `MIT License`. For further information please refer to the `LICENSE` file.
