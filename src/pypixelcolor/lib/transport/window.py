from dataclasses import dataclass

@dataclass
class Window:
    data: bytes
    requires_ack: bool = True
