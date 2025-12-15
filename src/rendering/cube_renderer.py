from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from .obj_loader import OBJLoader


class CubeRenderer:
    def __init__(self, obj_path: str | None = None):
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.scale = 1.0

        self.offset_x = 0.0
        self.offset_y = 0.0
        self.offset_z = 0.0

        if obj_path is not None:
            loader = OBJLoader(obj_path)

            # hitung centroid
            cx, cy, cz = loader.compute_centroid()
            print(f"[CubeRenderer] CENTROID: ({cx:.2f}, {cy:.2f}, {cz:.2f})")

            # SHIFT vertices langsung (bukan offset)
            self.vertices = [
                (v[0] - cx, v[1] - cy, v[2] - cz)
                for v in loader.vertices
            ]
            self.faces = loader.faces
            self.face_colors = loader.face_colors
            self.face_normals = loader.face_normals

            print(f"[CubeRenderer] vertices shifted by centroid")

        else:
            # fallback cube
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
                (0, 1, 2), (0, 2, 3),
                (4, 5, 6), (4, 6, 7),
                (0, 1, 5), (0, 5, 4),
                (2, 3, 7), (2, 7, 6),
                (1, 2, 6), (1, 6, 5),
                (0, 3, 7), (0, 7, 4),
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
        self.scale = scale * 0.1

    def init_gl(self, width: int = 800, height: int = 600):
        print("[CubeRenderer] init_gl")

        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 10.0, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))

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

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(
            0.0, 0.0, 7.0,
            0.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
        )

        # NO offset translate - vertices sudah di-shift
        glScalef(self.scale, self.scale, self.scale)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        glBegin(GL_TRIANGLES)
        for face, color, normal in zip(self.faces, self.face_colors, self.face_normals):
            glColor3f(*color)
            glNormal3f(*normal)
            for idx in face[:3]:
                x, y, z = self.vertices[idx]
                glVertex3f(x, y, z)
        glEnd()

        glutSwapBuffers()
