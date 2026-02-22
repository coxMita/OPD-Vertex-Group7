# Development Environment Setup
## Environment Variables
Before running the project, make sure to set up the required environment variables. You should create a `.env` file in the root directory of the project. It should contain the following variables:

```env
AMQP_URL=amqp://<user>:<password>@localhost:<port>/
DATABASE_URL=postgresql://<user>:<password>@localhost:<port>/booking_db
```
Replace `<user>`, `<password>`, and `<port>` with the appropriate values for your RabbitMQ and PostgreSQL instances. Make sure you use the same credentials defined in the `.env` file in the root directory of the whole project.

## uv
1. Download and install uv from the [Official Website](https://docs.astral.sh/uv/).
2. In the root directory of this project run the following command to install all dependencies:
    ```bash
    uv sync
    ```
   This will automatically create a virtual environment and install all required packages.
3. To run the project locally, use the command:
    ```bash
    uv run fastapi dev
    ```
   Make sure you to start the RabbitMQ and PostgreSQL services before running the booking service. You can use Docker to run these services as described below.

## pre-commit Hooks
To ensure code quality and consistency, pre-commit hooks are set up for this project. To install the pre-commit hooks, run the following command in the root directory of the project:
```bash
uv run pre-commit install
```
This will set up the pre-commit hooks to run automatically before each commit. You can also manually run the pre-commit checks on the staged files by executing:
```bash
uv run pre-commit run
```

## Docker
1. Make sure you have Docker installed on your machine. You can download it from the [Official Docker Website](https://www.docker.com/get-started).
2. In the root directory of the project, build the Docker image using the following command:
    ```bash
    docker build -t <docker image + :v1.0.0> .
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
5. If you only want to run specific services defined in the `docker-compose.yml` file, you can specify them by name:
    ```bash
    docker compose up -d booking-service booking-db rabbitmq
    ```
    This command will only start the `booking-service`, `booking-db`, and `rabbitmq` services.
6. To push the Docker image to Docker Hub, first log in to your Docker account:
    ```bash
    docker login
    ```
   Then, push the image using the following command:
    ```bash
    docker push 4<docker image + :v1.0.0>
    ```
   Make sure to replace `v1.0.0` with the appropriate version tag.

## Database Migration
To manage database migrations use Alembic. If Alembic has not been initialised yet, you can do so by running:
```bash
uv run alembic init migrations
```

Make sure to configure the `alembic.ini` file and the `env.py` file in the `migrations` directory to connect to your database using the `DATABASE_URL` environment variable.
Add all your database models' metadata to the `target_metadata` variable in the `env.py` by file by importing them to enable autogeneration of migrations.

Spin up the PostgreSQL database using Docker before running any migration commands.

```bash
docker compose up -d booking-db rabbitmq
```

Build the docker image first with:
```bash
docker build -t <docker image + :v1.0.0> .
```

Start the docker image with:
```bash
docker compose up -d booking-service
```

Connect to the running booking-service container:
```bash
docker exec -it booking-service bash
```

To create a new migration after making changes to the database models, run the following command inside the container:
```bash
uv run alembic revision --autogenerate -m "Your migration message"
```

Apply the migrations to the database using:
```bash
uv run alembic upgrade head
```

Exit the container:
```bash
exit
```

Change directory to the booking-service folder:
```bash
cd backend/booking-service
```

To commit the revision files, exit the container and copy the generated migration files from the container to your local machine.
```bash
docker cp booking-service:/app/migrations .
```

Commit the changes to git and push them to the repository.
```bash
git add migrations
git commit -m "feat: migrate database schema"
git push origin <branch-name>
```

### Common Alembic Commands
To create a new migration after making changes to the database models, run:
```bash
uv run alembic revision --autogenerate -m "Your migration message"
```
To apply the migrations to the database, use:
```bash
uv run alembic upgrade head
```
Make sure that the docker container for the database is running before applying the migrations.

To list all the tables in the database, you can use:
```bash
docker exec -it booking-db psql -U <user> -d <database> -c "\dt"
```
Replace `<user>` and `<database>` with the appropriate values for your PostgreSQL instance.

To view the current revision of the database, run:
```bash
uv run alembic current
```

To list the revision directly from the database, use:
```bash
docker exec -it booking-db psql -U booking_user -d booking_db -c "SELECT * FROM alembic_version;"
```

To downgrade the database to a previous version, use:
```bash
uv run alembic downgrade <revision>
```
Replace `<revision>` with the specific revision identifier you want to downgrade to. You can also use `-1` to downgrade one step.

If you want to undo the last migration you applied, you can run:
```bash
uv run alembic downgrade -1
```

## Additional Notes
- Use the pgadmin client to manage and view the PostgreSQL database. Use the credentials defined in the `.env` file in the root directory of the whole project.
- To access the PostgreSQL database from your terminal, you can use the following command:
```bash
docker exec -it booking-db psql -U <user> -d <database>
```
- Use the RabbitMQ management interface to monitor and manage RabbitMQ.