import os
import sys
from uuid import UUID
from keycloak import KeycloakAdmin
from sqlmodel import Session, create_engine, select
from dotenv import load_dotenv

# Adjust path to include src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.db.doctor import Doctor
from src.models.db.user import User

load_dotenv()

# Keycloak settings
# When running locally, use localhost:8089. In docker, would use keycloak:8080
KEYCLOAK_URL = os.getenv("KEYCLOAK_EXTERNAL_URL", "http://localhost:8089")
REALM = os.getenv("KEYCLOAK_REALM", "opd-vertex")
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# DB settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user_user:user_pass@localhost:5435/user_db")

engine = create_engine(DATABASE_URL)

def sync():
    """Sync Keycloak users to the local Doctor database."""
    print(f"Connecting to Keycloak at {KEYCLOAK_URL}...")
    try:
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_URL,
            username=ADMIN_USER,
            password=ADMIN_PASS,
            realm_name=REALM,
            user_realm_name="master",
            verify=True
        )

        users = keycloak_admin.get_users({})
        print(f"Found {len(users)} users in Keycloak.")

        with Session(engine) as session:
            for k_user in users:
                user_name = k_user.get("username")
                if user_name == "admin":
                    continue
                
                k_id = UUID(k_user["id"])
                k_email = k_user.get("email", f"{user_name}@example.com")
                first_name = k_user.get("firstName", "")
                last_name = k_user.get("lastName", "")
                full_name = f"{first_name} {last_name}".strip() or user_name

                # 1. Ensure User entry exists
                existing_user = session.get(User, k_id)
                if not existing_user:
                    print(f"Adding User record for {user_name}...")
                    session.add(User(user_id=k_id))
                
                # 2. Ensure Doctor entry exists (Colleagues are doctors)
                statement = select(Doctor).where(Doctor.keycloak_id == k_id)
                existing_doctor = session.exec(statement).first()
                
                if not existing_doctor:
                    print(f"Adding Colleague {full_name} as a Doctor...")
                    doctor = Doctor(
                        full_name=full_name,
                        department_name="General Practice",  # Default department
                        email=k_email,
                        keycloak_id=k_id
                    )
                    session.add(doctor)
                else:
                    # Update email if changed
                    if existing_doctor.email != k_email:
                        existing_doctor.email = k_email
                        print(f"Updated email for {full_name}.")
                    print(f"Doctor {full_name} already exists.")
            
            session.commit()
            print("Successfully synchronized Keycloak users with the database.")

    except Exception as e:
        print(f"Error during synchronization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sync()
