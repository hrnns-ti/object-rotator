from src.numerical_methods import KalmanFilterTracker, ExponentialSmoothing

if __name__ == "__main__":
    kf = KalmanFilterTracker()
    sm = ExponentialSmoothing(alpha=0.7)

    print(kf.get_name())
    print("Kalman:", kf.apply(100, 200))

    print(sm.get_name())
    print("Smooth:", sm.apply(100, 200))
    print("Smooth next:", sm.apply(110, 210))
