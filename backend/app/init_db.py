from app.core.database import engine
from app.models.server import Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("ServerPulse database tables initialized.")
