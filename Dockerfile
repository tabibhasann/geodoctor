FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY . .
RUN pip install --no-cache-dir -e .
ENTRYPOINT ["geodoctor"]
CMD ["--help"]
LABEL org.opencontainers.image.title="geodoctor" \
      org.opencontainers.image.source="https://github.com/tabibhasan/geodoctor" \
      org.opencontainers.image.licenses="MIT"
