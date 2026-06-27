from dataclasses import dataclass, field


@dataclass
class Transform:
    location: tuple = (0, 0, 0)
    rotation: tuple = (0, 0, 0)
    
@dataclass
class FileInstance:
    file_path: str = ""
    transform: Transform = field(default_factory=Transform)