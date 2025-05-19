FROM ubuntu:latest
LABEL authors="vali"

ENTRYPOINT ["top", "-b"]