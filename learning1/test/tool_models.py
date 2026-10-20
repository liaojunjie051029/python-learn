from dataclasses import dataclass

@dataclass
class Tool:
    name: str
    description: str
    enabled: bool = True

    def summary(self) ->str:
        return f"{self.name}: {self.description},{"启用" if self.enabled else "禁用"} "