# Secret Santa
This is a web app that doesn't require some BS sign up data harvesting. It's simple, and that's the point.

## Screenshots

<img width="949" height="542" alt="image" src="https://github.com/user-attachments/assets/e64d6319-a210-4534-982a-89c8c9e12157" />

<img width="622" height="476" alt="image" src="https://github.com/user-attachments/assets/0cb5e4c7-7887-455b-8ca8-8a7ba7b7fb71" />

Configurable question set

<img width="787" height="743" alt="image" src="https://github.com/user-attachments/assets/71ff5f65-0fe2-41bc-934f-6d8b212348f7" />

First registered user is the admin

<img width="743" height="395" alt="image" src="https://github.com/user-attachments/assets/0c36e837-1666-42fd-b134-475288dd47f9" />

Includes restrictions for assignments

<img width="780" height="423" alt="image" src="https://github.com/user-attachments/assets/69ad735f-13d4-42e2-a9d2-85ec5791e468" />

After everyone registers, admin starts assignments.
Then each participant is given their assigned person.

<img width="553" height="682" alt="image" src="https://github.com/user-attachments/assets/c0d81d98-908a-4057-afe5-961021dab7ce" />


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
