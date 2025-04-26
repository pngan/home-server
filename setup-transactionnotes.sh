#!/usr/bin/bash
docker compose down apiservice
docker compose down webfrontend
docker compose down centraldb-migration
docker compose pull apiservice
docker compose pull webfrontend
docker compose pull centraldb-migration

docker compose up -d
