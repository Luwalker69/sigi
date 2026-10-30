# Image sandbox de SIGI : le rayon d'explosion est le conteneur.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

CMD ["bash"]
