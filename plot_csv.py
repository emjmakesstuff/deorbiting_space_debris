import argparse
import numpy as np
import matplotlib.pyplot as plt

MA_WINDOW_S = 0.20
LOWPASS_FC = 5.0


def load_csv(path):
    current = []
    timestamps = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            fields = s.split(",")
            current.append(float(fields[0]))
            if len(fields) >= 2:
                timestamps.append(int(fields[-1]))

    current = np.array(current, float)

    if timestamps:
        t = (np.array(timestamps, float) - timestamps[0]) / 1000.0
    else:
        dt = 0.010
        t = np.arange(len(current)) * dt

    return t, current


def trim(t, y, t_start, t_end):
    mask = t >= t_start
    if t_end is not None:
        mask &= t <= t_end
    t = t[mask] - t[mask][0]
    y = y[mask]
    return t, y


def apply_filter(t, y, mode):
    if mode == "none":
        return y.copy()

    dt = np.median(np.diff(t)) if len(t) > 1 else 0.010

    if mode == "moving_average":
        w = max(1, int(round(MA_WINDOW_S / dt)))
        kernel = np.ones(w) / w
        return np.convolve(y, kernel, mode="same")

    if mode == "lowpass_1pole":
        alpha = (2 * np.pi * LOWPASS_FC * dt) / (1 + 2 * np.pi * LOWPASS_FC * dt)
        y_f = np.empty_like(y)
        y_f[0] = y[0]
        for n in range(1, len(y)):
            y_f[n] = y_f[n - 1] + alpha * (y[n] - y_f[n - 1])
        return y_f

    raise ValueError(f"Unknown filter mode: {mode}")


def plot(t, y, y_filtered, filter_mode):
    plt.figure()
    plt.plot(t, y, label="raw", alpha=0.5)
    if filter_mode != "none":
        plt.plot(t, y_filtered, label=f"filtered ({filter_mode})", linewidth=2)
    plt.grid(True)
    plt.xlabel("Time (s)")
    plt.ylabel("Current")
    plt.legend()
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot current data from Arduino CSV")
    parser.add_argument("csv_file", help="Path to the CSV file")
    parser.add_argument("--t-start", type=float, default=0, help="Trim: start time in seconds (default: 0)")
    parser.add_argument("--t-end", type=float, default=None, help="Trim: end time in seconds (default: None)")
    parser.add_argument("--filter", choices=["none", "moving_average", "lowpass_1pole"],
                        default="moving_average", help="Filter mode (default: moving_average)")
    args = parser.parse_args()

    t, current = load_csv(args.csv_file)
    t, current = trim(t, current, args.t_start, args.t_end)
    filtered = apply_filter(t, current, args.filter)
    plot(t, current, filtered, args.filter)


if __name__ == "__main__":
    main()
