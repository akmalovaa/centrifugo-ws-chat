import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    log_level: str = "INFO"
    centrifugo_url: str = "http://centrifugo:8000"
    centrifugo_socket_url: str = "ws://localhost:8000/connection/websocket"
    centrifugo_api_key: str = "api_key"
    centrifugo_secret: str = "secret"
    centrifugo_channel: str = "chat"


settings: Settings = Settings()
