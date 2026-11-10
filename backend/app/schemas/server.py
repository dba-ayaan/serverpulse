from pydantic import BaseModel, ConfigDict, Field


class ServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    hostname: str = Field(min_length=1, max_length=255)
    environment: str = Field(default="DEV", max_length=30)
    exporter_port: int = Field(default=9100, ge=1, le=65535)


class ServerResponse(ServerCreate):
    id: int
    enabled: bool

    model_config = ConfigDict(from_attributes=True)
