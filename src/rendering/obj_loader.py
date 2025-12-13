import os
from typing import List, Tuple, Dict, Optional

class OBJLoader:
    def __init__(self, path: str):
        self.vertices: List[Tuple[float, float, float]] = []
        self.faces: List[Tuple[int, int, int]] = []
        self.face_colors: List[Tuple[float, float, float]] = []
        self._load(path)

    def _load(self, path: str):
        base_dir = os.path.dirname(path)
        current_color: Tuple[float, float, float] = (0.8, 0.8, 0.8)
        mtl_colors: Dict[str, Tuple[float, float, float]] = {}

        with open(path, "r") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if line.startswith("mtllib"):
                _, mtl_name = line.split(maxsplit=1)
                mtl_path = os.path.join(base_dir, mtl_name)
                mtl_colors = self._load_mtl(mtl_path)
                break

        current_material: Optional[str] = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("usemtl"):
                _, mat_name = line.split(maxsplit=1)
                current_material = mat_name.strip()
                current_color = mtl_colors.get(current_material, (0.8, 0.8, 0.8))

            elif line.startswith("v "):
                parts = line.split()
                if len(parts) >= 4:
                    _, x, y, z = parts[:4]
                    self.vertices.append((float(x), float(y), float(z)))

            elif line.startswith("f "):
                parts = line.split()[1:]
                idx = []
                for p in parts[:3]:
                    v_idx = p.split("/")[0]
                    idx.append(int(v_idx) - 1)
                if len(idx) == 3:
                    self.faces.append(tuple(idx))
                    self.face_colors.append(current_color)

        print(f"[OBJLoader] loaded {len(self.vertices)} vertices, {len(self.faces)} faces, {len(mtl_colors)} materials")

    def _load_mtl(self, mtl_path: str) -> Dict[str, Tuple[float, float, float]]:
        colors: Dict[str, Tuple[float, float, float]] = {}
        if not os.path.exists(mtl_path):
            print(f"[OBJLoader] MTL not found: {mtl_path}")
            return colors

        current_name: Optional[str] = None

        with open(mtl_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("newmtl"):
                    _, name = line.split(maxsplit=1)
                    current_name = name.strip()
                elif line.startswith("Kd") and current_name is not None:
                    parts = line.split()
                    if len(parts) >= 4:
                        _, r, g, b = parts[:4]
                        colors[current_name] = (float(r), float(g), float(b))

        print(f"[OBJLoader] loaded {len(colors)} materials from {mtl_path}")
        return colors
