## Docker
1. Make sure you have Docker installed on your machine. You can download it from the [Official Docker Website](https://www.docker.com/get-started).
2. In the root directory of the project, build the Docker image using the following command:
    ```bash
    docker build -t mita28/opdvertex:ai-service-1.0.0 .
    ```
   Make sure to replace `v1.0.0` with the desired version tag.
3. Once the image is built, you can run the container with docker compose with the `docker-compose.yml` file provided in the root directory of the whole project:
    ```bash
    docker compose up -d
    ```
   This will start the booking service along with any other services defined in the `docker-compose.yml` file. Make sure that the correct tag is used in the `docker-compose.yml` file for the booking service image. Docker will use the local image if it finds one with the specified tag. Otherwise, it will pull the image from the Docker registry.
4. To stop the running containers, use the command:
    ```bash
    docker compose down
    ```
6. To push the Docker image to Docker Hub, first log in to your Docker account:
    ```bash
    docker login
    ```
   Then, push the image using the following command:
    ```bash
    docker push mita28/opdvertex:ai-service-1.0.0
    ```
   Make sure to replace `v1.0.0` with the appropriate version tag.

