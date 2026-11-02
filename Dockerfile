FROM ubuntu:latest
LABEL authors="rorok"

ENTRYPOINT ["top", "-b"]