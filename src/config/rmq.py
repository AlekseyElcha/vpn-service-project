from pydantic import BaseModel


class RabbitMQConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str

    @property
    def rmq_connection_url(self):
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/%2f"
