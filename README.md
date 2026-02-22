# OPD-Vertex-Group7
OPD Vertex project repository of Group 7

    For each DB-backed service:
        cd backend/<service>
        uv run alembic init migrations
        
    Build docker-compose.yml and start:
        docker compose up -d