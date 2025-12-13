import cv2
import numpy as np
from OpenGL.raw.GLUT import glutPostRedisplay
from cvzone.HandTrackingModule import HandDetector

import threading
import queue

from src.controllers.hand_controller import HandTrackingController
from src.rendering.cube_renderer import CubeRenderer


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    detector = HandDetector(detectionCon=0.8, maxHands=2)

    # TANGAN KIRI - SMOOTHING
    rot_ctrl = HandTrackingController()
    rot_ctrl.set_mode(3)

    scale = 1.0
    scale_alpha = 0.2
    prev_left_pos = None

    # nilai rotasi global
    rot_x = 0.0
    rot_y = 0.0

    # queue untuk kirim data ke thread OpenGL
    render_queue = queue.Queue()
    cube = CubeRenderer(obj_path="models/Lowpoly_tree_sample.obj")  # path .obj

    # ================= THREAD OPENGL ================= #
    def gl_thread():
        from OpenGL.GLUT import (
            glutInit, glutInitDisplayMode, glutInitWindowSize,
            glutCreateWindow, glutDisplayFunc, glutIdleFunc, glutMainLoop,
            GLUT_DOUBLE, GLUT_RGBA, GLUT_DEPTH
        )

        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
        glutInitWindowSize(800, 600)
        glutCreateWindow(b"3D Object")

        cube.init_gl(800, 600)

        def display():
            try:
                rot_x_val, rot_y_val, scale_val = render_queue.get_nowait()
                cube.update_state(rot_x_val, rot_y_val, scale_val)
            except queue.Empty:
                pass
            cube.draw()
            glutPostRedisplay()

        glutDisplayFunc(display)
        glutIdleFunc(display)
        glutMainLoop()

    t = threading.Thread(target=gl_thread, daemon=True)
    t.start()
    # ================================================= #

    while True:
        success, frame = cap.read()
        if not success:
            break

        # flip dan pakai satu variabel gambar: img
        img = cv2.flip(frame, 1)
        hands, img = detector.findHands(img, flipType=False)

        rot_vector = (0.0, 0.0)

        # POSISI TANGAN
        if hands:
            hands = sorted(hands, key=lambda h: h['center'][0])

            # TANGAN KIRI || ROTASI
            if len(hands) >= 1:
                left = hands[0]
                lmL = left['lmList']
                ixL, iyL, _ = lmL[8]

                xL_raw, yL_raw = float(ixL), float(iyL)
                xL_filter, yL_filter = rot_ctrl.process(xL_raw, yL_raw)

                # GAMBAR TITIK
                cv2.circle(img, (int(xL_raw), int(yL_raw)), 7, (0, 0, 255), -1)
                cv2.circle(img, (int(xL_filter), int(yL_filter)), 7, (0, 255, 0), 2)

                # HITUNG DELTA
                if prev_left_pos is not None:
                    dx = xL_filter - prev_left_pos[0]
                    dy = yL_filter - prev_left_pos[1]
                    rot_vector = (dx, dy)
                prev_left_pos = (xL_filter, yL_filter)

            # TANGAN KANAN || SCALE
            if len(hands) >= 2:
                right = hands[1]
                lmR = right['lmList']
                x_thumb, y_thumb, _ = lmR[4]  # THUMBS
                x_idx, y_idx, _ = lmR[8]      # POINTER

                # EUCLIDEAN 2D
                dist = np.hypot(x_idx - x_thumb, y_idx - y_thumb)

                # MAX DISTANCE
                d_min, d_max = 30.0, 200.0
                s_min, s_max = 0.5, 2.0
                d_clamped = max(d_min, min(d_max, dist))
                t_norm = (d_clamped - d_min) / (d_max - d_min)
                target_scale = s_min + t_norm * (s_max - s_min)

                # SIMPLE SMOOTH
                scale = (1 - scale_alpha) * scale + scale_alpha * target_scale

                # GAMBAR GARIS
                cv2.line(img, (int(x_thumb), int(y_thumb)),
                         (int(x_idx), int(y_idx)), (255, 0, 0), 2)
                cv2.putText(img, f"dist={int(dist)} scale={scale:.2f}",
                            (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (0, 255, 255), 2)

        # integrasi rotasi dari vektor gerak tangan kiri
        dx, dy = rot_vector
        dead = 1.0
        if abs(dx) < dead:
            dx = 0.0
        if abs(dy) < dead:
            dy = 0.0

        rot_speed_x = -dy * 0.05  # dy -> rot_x
        rot_speed_y =  dx * 0.05  # dx -> rot_y
        rot_x += rot_speed_x
        rot_y += rot_speed_y

        # kirim state ke renderer (kalau queue lagi kosong)
        if render_queue.empty():
            render_queue.put((rot_x, rot_y, scale))

        # INFO ROTASI
        cv2.putText(
            img,
            f"Rot vec (dx, dy) = ({rot_vector[0]:.1f}, {rot_vector[1]:.1f})",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        cv2.putText(
            img,
            f"rot_x={rot_x:.2f} rot_y={rot_y:.2f} scale={scale:.2f}",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        cv2.putText(
            img,
            "Left hand: rotation  |  Right hand: scale (thumb-index distance)",
            (20, img.shape[0] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            2,
        )

        cv2.imshow("Two-Hand Control (Rotation + Scale)", img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('1'):
            rot_ctrl.set_mode(1)
        elif key == ord('2'):
            rot_ctrl.set_mode(2)
        elif key == ord('3'):
            rot_ctrl.set_mode(3)
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
