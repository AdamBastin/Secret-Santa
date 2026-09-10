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
