from dataclasses import dataclass
from dataclasses import field


@dataclass
class D:
    x: dict[int, int] = field(default_factory=lambda: {})


d1 = D()
d1.x[1] = 1

d2 = D()
d2.x[1] = 2
d2.x[1] += 1

print(d1.x)
print(d2.x)
