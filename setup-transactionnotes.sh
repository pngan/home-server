#!/usr/bin/bash
echo "============================================================================="
echo "Don't forget to update docker-compose.yaml to point to the latest image tags!"
echo "============================================================================="
echo
docker compose down apiservice
docker compose down webfrontend
docker compose down centraldb-migration
docker compose pull apiservice
docker compose pull webfrontend
docker compose pull centraldb-migration

docker compose up -d
