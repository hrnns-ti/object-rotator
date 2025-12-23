from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from .obj_loader import OBJLoader


class CubeRenderer:
    def __init__(self, obj_path: str | None = None):
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.scale = 1.0

        # display list id (dibuat di init_gl)
        self.gl_list: int | None = None

        if obj_path is not None:
            loader = OBJLoader(obj_path)

            # hitung centroid supaya pivot di tengah objek
            cx, cy, cz = loader.compute_centroid()
            print(f"[CubeRenderer] CENTROID: ({cx:.2f}, {cy:.2f}, {cz:.2f})")

            # geser vertex sehingga pusat objek di (0,0,0)
            self.vertices = [
                (v[0] - cx, v[1] - cy, v[2] - cz)
                for v in loader.vertices
            ]
            # faces = List[List[int]] (bisa 3,4,5,... vertex)
            self.faces = loader.faces
            self.face_colors = loader.face_colors
            self.face_normals = loader.face_normals

            print("[CubeRenderer] vertices shifted by centroid")

        else:
            # fallback cube (face disimpan sebagai quad, akan di-fan-triangulate)
            self.vertices = [
                (-1, -1, -1),
                (1, -1, -1),
                (1, 1, -1),
                (-1, 1, -1),
                (-1, -1, 1),
                (1, -1, 1),
                (1, 1, 1),
                (-1, 1, 1),
            ]
            self.faces = [
                [0, 1, 2, 3],  # belakang
                [4, 5, 6, 7],  # depan
                [0, 1, 5, 4],  # bawah
                [2, 3, 7, 6],  # atas
                [1, 2, 6, 5],  # kanan
                [0, 3, 7, 4],  # kiri
            ]
            self.face_colors = [(0.7, 0.7, 1.0)] * len(self.faces)
            self.face_normals = [(0.0, 0.0, 1.0)] * len(self.faces)

        print(
            f"[CubeRenderer] mesh loaded: {len(self.vertices)} vertices, "
            f"{len(self.faces)} faces"
        )

    def update_state(self, rot_x: float, rot_y: float, scale: float):
        self.rot_x = rot_x
        self.rot_y = rot_y
        # skala global dibatasi supaya tidak terlalu besar
        self.scale = scale * 0.1

    def init_gl(self, width: int = 800, height: int = 600):
        print("[CubeRenderer] init_gl")

        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)

        # lighting dasar
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (15.0, 15.0, 20.0, 0.3))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.1, 0.1, 0.1, 0.1))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 0.1))

        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / float(height), 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # ====== BANGUN DISPLAY LIST SEKALI SAJA ======
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)

        glBegin(GL_TRIANGLES)
        for verts, color, normal in zip(self.faces, self.face_colors, self.face_normals):
            if len(verts) < 3:
                continue

            glColor3f(*color)
            glNormal3f(*normal)

            # fan triangulation: (v0,v1,v2), (v0,v2,v3), ...
            v0 = verts[0]
            x0, y0, z0 = self.vertices[v0]

            for i in range(1, len(verts) - 1):
                i1 = verts[i]
                i2 = verts[i + 1]

                x1, y1, z1 = self.vertices[i1]
                x2, y2, z2 = self.vertices[i2]

                glVertex3f(x0, y0, z0)
                glVertex3f(x1, y1, z1)
                glVertex3f(x2, y2, z2)
        glEnd()

        glEndList()
        # ====== END DISPLAY LIST ======

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(
            0.0, 0.0, 7.0,   # posisi kamera
            0.0, 0.0, 0.0,   # titik yang dilihat
            0.0, 1.0, 0.0,   # up vector
        )

        glScalef(self.scale, self.scale, self.scale)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        # panggil display list (sangat ringan per-frame)
        if self.gl_list is not None:
            glCallList(self.gl_list)

        glutSwapBuffers()
