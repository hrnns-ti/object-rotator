import os
from typing import List, Tuple, Dict, Optional


class OBJLoader:
    def __init__(self, path: str):
        self.vertices: List[Tuple[float, float, float]] = []
        self.faces: List[Tuple[int, int, int]] = []
        self.face_colors: List[Tuple[float, float, float]] = []
        self.face_normals: List[Tuple[float, float, float]] = []

        self._load(path)

    def _load(self, path: str):
        base_dir = os.path.dirname(path)
        current_color: Tuple[float, float, float] = (0.8, 0.8, 0.8)
        mtl_colors: Dict[str, Tuple[float, float, float]] = {}

        with open(path, "r") as f:
            lines = f.readlines()

        # cari dan load .mtl
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
                idx: List[int] = []
                for p in parts[:3]:
                    v_idx = p.split("/")[0]
                    idx.append(int(v_idx) - 1)

                if len(idx) == 3:
                    self.faces.append(tuple(idx))
                    self.face_colors.append(current_color)

                    # hitung normal face
                    v0 = self.vertices[idx[0]]
                    v1 = self.vertices[idx[1]]
                    v2 = self.vertices[idx[2]]
                    nx, ny, nz = self._compute_normal(v0, v1, v2)
                    self.face_normals.append((nx, ny, nz))

        print(
            f"[OBJLoader] loaded {len(self.vertices)} vertices, "
            f"{len(self.faces)} faces, {len(mtl_colors)} materials"
        )

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

    def _compute_normal(
        self,
        v0: Tuple[float, float, float],
        v1: Tuple[float, float, float],
        v2: Tuple[float, float, float],
    ) -> Tuple[float, float, float]:
        # v0, v1, v2 = (x, y, z)
        x1, y1, z1 = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
        x2, y2, z2 = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]

        # cross product
        nx = y1 * z2 - z1 * y2
        ny = z1 * x2 - x1 * z2
        nz = x1 * y2 - y1 * x2

        length = (nx * nx + ny * ny + nz * nz) ** 0.5
        if length == 0:
            return 0.0, 0.0, 1.0
        return nx / length, ny / length, nz / length
