# seed.py
from database import SessionLocal
from models.role_model import Role
from models.user_model import User
from models.notification_model import Notification
from models.history_model import History
from models.location_model import Location
from models.cctv_model import CctvCamera

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_roles(db):
    default_roles = ["Superadmin", "Security"]

    for role_name in default_roles:
        existing = db.query(Role).filter(Role.nama_role == role_name).first()
        if not existing:
            new_role = Role(nama_role=role_name)
            db.add(new_role)
            print(f"Role ditambahkan: {role_name}")
        else:
            print(f"Role sudah ada: {role_name}")

    db.commit()


def create_default_user(db):
    # cek role superadmin
    role = db.query(Role).filter(Role.nama_role == "Superadmin").first()
    if not role:
        print("Role superadmin belum ada. Jalankan create_roles() dulu.")
        return

    # cek user superadmin
    existing = db.query(User).filter(User.username == "superadmin").first()
    if existing:
        print("User superadmin sudah ada")
        return

    hashed_pw = pwd_context.hash("Rsch123")

    user = User(
        nama="Super Admin",
        nik="1234.67890",
        username="satya123",
        password=hashed_pw,
        id_role=role.id_role
    )

    db.add(user)
    db.commit()
    print("User superadmin dibuat")


def run_seed():
    db = SessionLocal()

    print("\n=== Menjalankan Seeder ===")
    create_roles(db)
    create_default_user(db)
    db.close()
    print("=== Seeder Selesai ===\n")


if __name__ == "__main__":
    run_seed()
