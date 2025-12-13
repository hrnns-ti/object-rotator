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
        self.offset_y = -1.0
        self.offset_z = 0.0

        if obj_path is not None:
            loader = OBJLoader(obj_path)
            self.vertices = loader.vertices           # list[(x,y,z)]
            self.faces = loader.faces                 # list[(i,j,k)]
        else:
            self.vertices = [
                (-1, -1, -1),
                ( 1, -1, -1),
                ( 1,  1, -1),
                (-1,  1, -1),
                (-1, -1,  1),
                ( 1, -1,  1),
                ( 1,  1,  1),
                (-1,  1,  1),
            ]
            self.faces = [
                (0, 1, 2), (0, 2, 3),
                (4, 5, 6), (4, 6, 7),
                (0, 1, 5), (0, 5, 4),
                (2, 3, 7), (2, 7, 6),
                (1, 2, 6), (1, 6, 5),
                (0, 3, 7), (0, 7, 4),
            ]

        print(f"[CubeRenderer] mesh loaded: {len(self.vertices)} vertices, {len(self.faces)} faces")

    def update_state(self, rot_x: float, rot_y: float, scale: float):
        self.rot_x = rot_x
        self.rot_y = rot_y
        self.scale = scale * 0.2

    def init_gl(self, width: int = 800, height: int = 600):
        print("[CubeRenderer] init_gl")
        glClearColor(0.1, 0.1, 0.1, 1)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        glViewport(0, 0, width, height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / float(height), 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # kamera
        gluLookAt(0.0, 0.0, 7.0,
                  0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0)

        glTranslatef(self.offset_x, self.offset_y, self.offset_z)

        glScalef(self.scale, self.scale, self.scale)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        glBegin(GL_TRIANGLES)
        glColor3f(0.2, 0.8, 0.3)
        for face in self.faces:          # face = (i,j,k)
            for idx in face[:3]:
                x, y, z = self.vertices[idx]
                glVertex3f(x, y, z)
        glEnd()

        glutSwapBuffers()
