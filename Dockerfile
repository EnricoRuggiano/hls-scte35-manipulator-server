FROM python:3.12-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /src

COPY pyproject.toml requirements.txt ./
COPY hls_scte35_manipulator_server ./hls_scte35_manipulator_server

RUN    python -m pip install --no-cache-dir --upgrade pip build \
    && python -m build --wheel --outdir /dist

FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup -S app && adduser -S app -G app

COPY --from=builder /dist/*.whl /tmp/
RUN    python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir /tmp/*.whl \
    && rm -f /tmp/*.whl

# add only profile json files
COPY hls_scte35_manipulator_server/profiles/*.json ./profiles/

USER app

EXPOSE 4999 

ENTRYPOINT ["hls-scte35-manipulator-server"]
CMD ["--origin-base-url", "http://host.docker.internal:5000", "--profile", "profiles/profile.json", "--host", "0.0.0.0", "--port", "4999"]
