#!/usr/bin/bash
docker compose down apiservice
docker compose down webfrontend
docker compose pull apiservice
docker compose pull webfrontend

docker compose up -d
