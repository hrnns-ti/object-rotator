import numpy as np
from typing import Tuple
from .base_tracker import Base

class KalmanFilterTracker(Base):
    def __init__(self):
        # PREDIKSI KEMANA
        self.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

        # KAMERA LIAT APA (X,Y)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ], dtype=np.float32)

        self.Q = np.eye(4, dtype=np.float32) * 0.03
        self.R = np.eye(2, dtype=np.float32) * 0.1

        self.x = np.zeros((4, 1) dtype=np.float32)
        self.p = np.zeros((4) dtype=np.float32)* 10

    def apply(self, x: float, y:float) -> Tuple[float, float]:
        z = np.array([[x, y]], dtype=np.float32)