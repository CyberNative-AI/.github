#!/bin/sh
# The 12 test files for the check line in the note. Expect 7 matches (a-g) and none in h-k or node_modules.
set -eu
T=$(mktemp -d); cd "$T"; mkdir -p a b c d e f g h i j k node_modules/x
printf 'FROM node:lts\n' > a/Dockerfile
printf 'FROM node:lts-trixie-slim AS base\n' > b/Dockerfile
printf 'FROM --platform=$BUILDPLATFORM node:lts-alpine AS build\n' > c/Dockerfile.prod
printf 'from node\n' > d/Dockerfile
printf 'FROM docker.io/library/node:latest\n' > e/Dockerfile
printf 'image: node:lts\n' > f/.gitlab-ci.yml
printf '    image: "node:current-alpine"\n' > g/docker-compose.yml
printf 'FROM node:24-slim\n' > h/Dockerfile
printf 'FROM node:26.11.1\nFROM nodejs:lts\n' > i/Dockerfile
printf 'FROM node:lts@sha256:abc\n' > j/Dockerfile
printf 'FROM mynode:lts\nimage: node:24\n' > k/Dockerfile
printf 'FROM node:lts\n' > node_modules/x/Dockerfile
grep -rnEi --exclude-dir=node_modules "(^[[:space:]]*FROM[[:space:]]+(--platform=[^[:space:]]+[[:space:]]+)?|image:[[:space:]]*[\"']?)(docker\.io/)?(library/)?node(:(lts|latest|current|slim|alpine|bookworm|trixie)[^@[:space:]\"']*)?([\"']?[[:space:]]|[\"']?$)" .
