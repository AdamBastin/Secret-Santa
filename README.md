## Docker

Build the image:

```sh
docker build -t secret-santa .
```

Run the app with persistent local SQLite data:

```sh
docker run --rm -p 8000:8000 -v secret-santa-data:/app/instance secret-santa
```

Open http://localhost:8000.

Run from Docker Hub with Compose:

```sh
SECRET_SANTA_IMAGE=docker.io/your-dockerhub-username/secret-santa:latest docker compose up -d
```

Set `TEMPLATE_LINK` to the Docker Hub or deployment-template URL you want associated with the container.
