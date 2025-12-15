import cv2
import numpy as np
from OpenGL.raw.GLUT import glutPostRedisplay
from cvzone.HandTrackingModule import HandDetector

import threading
import queue
import time

from src.controllers.hand_controller import HandTrackingController
from src.rendering.cube_renderer import CubeRenderer


def main():
    global rot_dy_smooth, rot_dx_smooth
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    detector = HandDetector(detectionCon=0.8, maxHands=2)

    # TANGAN KIRI - SMOOTHING (untuk rotasi)
    rot_ctrl = HandTrackingController()
    rot_ctrl.set_mode(3)

    scale = 1.0
    scale_alpha = 0.2
    prev_left_pos = None
    baseline_left_pos = None  # baseline untuk delta
    last_baseline_time = time.time()
    baseline_interval = 1

    # nilai rotasi global
    rot_x = 0.0
    rot_y = 0.0

    # queue untuk kirim data ke thread OpenGL
    render_queue = queue.Queue()
    cube = CubeRenderer(obj_path="models/Lowpoly_tree_sample.obj")

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

        img = cv2.flip(frame, 1)
        hands, img = detector.findHands(img, flipType=False)

        rot_vector = (0.0, 0.0)
        current_time = time.time()

        # POSISI TANGAN
        if hands:
            hands = sorted(hands, key=lambda h: h['center'][0])

            # TANGAN KIRI || ROTASI
            if len(hands) >= 1:
                left = hands[0]
                xL_raw, yL_raw = left['center']
                xL_filter, yL_filter = rot_ctrl.process(float(xL_raw), float(yL_raw))

                # GAMBAR TITIK CENTER TANGAN
                cv2.circle(img, (int(xL_raw), int(yL_raw)), 7, (0, 0, 255), -1)
                cv2.circle(img, (int(xL_filter), int(yL_filter)), 7, (0, 255, 0), 2)

                # INIT baseline kalau belum ada
                if baseline_left_pos is None:
                    baseline_left_pos = (xL_filter, yL_filter)

                # HITUNG DELTA dari baseline
                dx = xL_filter - baseline_left_pos[0]
                dy = yL_filter - baseline_left_pos[1]
                rot_vector = (dx, dy)

                cv2.circle(
                    img,
                    (int(baseline_left_pos[0]), int(baseline_left_pos[1])),
                    7,
                    (255, 0, 0), 2
                )
                cv2.line(
                    img,
                    (int(baseline_left_pos[0]), int(baseline_left_pos[1])),
                    (int(xL_filter), int(yL_filter)),
                    (255, 0, 0), 1
                )

                # AUTO-RESET baseline setiap N detik
                if current_time - last_baseline_time > baseline_interval:
                    baseline_left_pos = (xL_filter, yL_filter)
                    last_baseline_time = current_time

            # TANGAN KANAN || SCALE
            if len(hands) >= 2:
                right = hands[1]
                lmR = right['lmList']
                x_thumb, y_thumb, _ = lmR[4]
                x_idx, y_idx, _ = lmR[8]

                dist = np.hypot(x_idx - x_thumb, y_idx - y_thumb)

                d_min, d_max = 30.0, 200.0
                s_min, s_max = 0.5, 2.0
                d_clamped = max(d_min, min(d_max, dist))
                t_norm = (d_clamped - d_min) / (d_max - d_min)
                target_scale = s_min + t_norm * (s_max - s_min)

                scale = (1 - scale_alpha) * scale + scale_alpha * target_scale

                cv2.line(img, (int(x_thumb), int(y_thumb)),
                         (int(x_idx), int(y_idx)), (255, 0, 0), 2)
                cv2.putText(img, f"dist={int(dist)} scale={scale:.2f}",
                            (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (0, 255, 255), 2)
        else:
            # kalau tidak ada tangan terdeteksi, reset baseline
            baseline_left_pos = None

        # ==================== INTEGRASI ROTASI ==================== #
        dx, dy = rot_vector

        # smoothing ringan pada delta gerak
        smooth_alpha = 0.3  # makin kecil makin halus
        if 'rot_dx_smooth' not in globals():
            rot_dx_smooth = 0.0
            rot_dy_smooth = 0.0

        rot_dx_smooth = (1 - smooth_alpha) * rot_dx_smooth + smooth_alpha * dx
        rot_dy_smooth = (1 - smooth_alpha) * rot_dy_smooth + smooth_alpha * dy

        # deadzone
        dead = 1.0
        if abs(rot_dx_smooth) < dead:
            rot_dx_smooth = 0.0
        if abs(rot_dy_smooth) < dead:
            rot_dy_smooth = 0.0

        # kecepatan rotasi dari delta halus terhadap baseline
        rot_speed_x = -rot_dy_smooth * 0.04
        rot_speed_y = rot_dx_smooth * 0.04

        rot_x += rot_speed_x
        rot_y += rot_speed_y
        # ====================================================== #

        if render_queue.empty():
            render_queue.put((rot_x, rot_y, scale))

        # DEBUG INFO
        time_since_reset = current_time - last_baseline_time
        cv2.putText(
            img,
            f"Rot vec: ({rot_vector[0]:.1f}, {rot_vector[1]:.1f}) | Reset in {baseline_interval - time_since_reset:.1f}s",
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
            "Left hand (movement from baseline): rotation  |  Right hand (fingers): scale",
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
