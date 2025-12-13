from typing import List, Tuple

class OBJLoader:
    def __init__(self, path: str):
        self.vertices: List[Tuple[float, float, float]] = []
        self.faces: List[Tuple[int, int, int]] = []
        self._load(path)

    def _load(self, path: str):
        with open(path, "r") as f:
            for line in f:
                if line.startswith("v "):  # vertex
                    _, x, y, z = line.strip().split()[:4]
                    self.vertices.append((float(x), float(y), float(z)))
                elif line.startswith("f "):  # face (triangles)
                    parts = line.strip().split()[1:]
                    # format umum: f v1 v2 v3 atau f v1/... v2/... v3/...
                    idx = []
                    for p in parts[:3]:
                        v_idx = p.split("/")[0]
                        idx.append(int(v_idx) - 1)  # .obj pakai 1-based
                    if len(idx) == 3:
                        self.faces.append(tuple(idx))