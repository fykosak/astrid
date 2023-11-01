# Docker container
## Build
  - in root directory:
    ```
    podman build . -f docker/Dockerfile --tag astrid
    ```

## Run
```
podman run --rm --name astrid --volume "./config:/home/astrid/.astrid" --volume "./ssh:/home/astrid/.ssh" -p 8080:8080 astrid
```
