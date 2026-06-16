from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore
from scipy.signal import savgol_filter
from scipy.spatial.transform import Rotation

from plot_csv import load_csv, trim, apply_filter

POSE_TOPIC = "/vrpn_mocap/robot2/pose"

RESAMPLE_HZ = 100.0
MIN_DT_S = 0.004

YAW_SMOOTH_WINDOW_S = 1
YAW_SMOOTH_POLY = 2
OMEGAZ_SMOOTH_WINDOW_S = 0
OMEGAZ_SMOOTH_POLY = 2


def _odd_geq(n: int, minimum: int) -> int:
    n = max(int(n), int(minimum))
    if n % 2 == 0:
        n += 1
    return n


def _largest_odd_leq(n: int) -> int:
    n = int(n)
    if n % 2 == 0:
        n -= 1
    return max(n, 1)


def _clamp_savgol_window(win: int, n: int, poly: int) -> int:
    if n <= 1:
        return 1
    win = _odd_geq(win, poly + 2)
    if win > n:
        win = _largest_odd_leq(n)
    if win <= poly:
        win = _odd_geq(poly + 2, poly + 2)
        if win > n:
            win = _largest_odd_leq(n)
    return win


def load_rosbag_pose_quats_wxyz(bag_dir: Path, pose_topic: str) -> tuple[np.ndarray, np.ndarray]:
    typestore = get_typestore(Stores.ROS2_HUMBLE)

    times_raw = []
    quats_raw = []

    with Reader(bag_dir) as reader:
        conns = [c for c in reader.connections if c.topic == pose_topic]
        if not conns:
            topics = [(c.topic, c.msgtype) for c in reader.connections]
            raise RuntimeError(
                f"Topic not found: {pose_topic}\nAvailable:\n"
                + "\n".join([f"  {t} [{mt}]" for t, mt in topics])
            )

        for connection, timestamp, rawdata in reader.messages(connections=conns):
            msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
            o = msg.pose.orientation
            times_raw.append(timestamp * 1e-9)
            quats_raw.append([o.w, o.x, o.y, o.z])

    times_raw = np.asarray(times_raw, dtype=np.float64)
    quats_raw = np.asarray(quats_raw, dtype=np.float64)

    keep = np.ones(len(times_raw), dtype=bool)
    for i in range(1, len(times_raw)):
        if times_raw[i] - times_raw[i - 1] < MIN_DT_S:
            keep[i] = False

    times = times_raw[keep]
    quats = quats_raw[keep]

    quats /= np.linalg.norm(quats, axis=1, keepdims=True)
    for i in range(1, len(quats)):
        if np.dot(quats[i], quats[i - 1]) < 0:
            quats[i] *= -1

    return times, quats


def yaw_from_quats_rad(quats_wxyz: np.ndarray) -> np.ndarray:
    r = Rotation.from_quat(quats_wxyz[:, [1, 2, 3, 0]])
    return np.unwrap(r.as_euler("ZYX")[:, 0])


def yaw_to_omega_z(times: np.ndarray, yaw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    fs_hz = RESAMPLE_HZ
    dt = 1.0 / fs_hz
    t_u = np.arange(float(times[0]), float(times[-1]) + 1e-12, dt)

    yaw_u = np.interp(t_u, times, yaw)

    yaw_win = _clamp_savgol_window(int(round(YAW_SMOOTH_WINDOW_S * fs_hz)), len(yaw_u), YAW_SMOOTH_POLY)
    yaw_s = savgol_filter(yaw_u, yaw_win, YAW_SMOOTH_POLY)

    omega_z = np.gradient(yaw_s, dt)

    om_win = _clamp_savgol_window(int(round(OMEGAZ_SMOOTH_WINDOW_S * fs_hz)), len(omega_z), OMEGAZ_SMOOTH_POLY)
    omega_z = savgol_filter(omega_z, om_win, OMEGAZ_SMOOTH_POLY)

    return t_u, omega_z


def main():
    parser = argparse.ArgumentParser(description="Overlay angular velocity (from rosbag) and current (from Arduino CSV)")
    parser.add_argument("--ros-file", required=True, help="Path to rosbag directory (containing metadata.yaml)")
    parser.add_argument("--current-data", required=True, help="Path to Arduino current CSV")
    parser.add_argument("--t-start", type=float, default=0, help="Trim: start time in seconds")
    parser.add_argument("--t-end", type=float, default=None, help="Trim: end time in seconds")
    parser.add_argument("--filter", choices=["none", "moving_average", "lowpass_1pole"],
                        default="moving_average", help="Filter for current data")
    parser.add_argument("--topic", default=POSE_TOPIC, help=f"ROS pose topic (default: {POSE_TOPIC})")
    parser.add_argument("-o", "--output", default="combined_plot.png", help="Output image path")
    args = parser.parse_args()

    # Load rosbag angular velocity
    bag_dir = Path(args.ros_file)
    times_epoch_s, quats = load_rosbag_pose_quats_wxyz(bag_dir, args.topic)
    yaw = yaw_from_quats_rad(quats)
    t_omega_epoch, omega_z = yaw_to_omega_z(times_epoch_s, yaw)

    # Load current data with epoch timestamps
    current_vals = []
    current_epoch_s = []
    with open(args.current_data) as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            fields = s.split(",")
            if len(fields) < 2:
                continue
            try:
                current_vals.append(float(fields[0]))
                current_epoch_s.append(int(fields[-1]) / 1000.0)
            except ValueError:
                continue
    current = np.array(current_vals, dtype=np.float64)
    t_current_epoch = np.array(current_epoch_s, dtype=np.float64)

    # Use the earliest timestamp across both datasets as t=0
    t0 = min(t_omega_epoch[0], t_current_epoch[0])
    t_omega_rel = t_omega_epoch - t0
    t_current_rel = t_current_epoch - t0

    # Trim (without re-zeroing, to preserve alignment)
    if args.t_start > 0 or args.t_end is not None:
        for arr_t, arr_y, name in [(t_omega_rel, omega_z, "omega"), (t_current_rel, current, "current")]:
            mask = arr_t >= args.t_start
            if args.t_end is not None:
                mask &= arr_t <= args.t_end
            if name == "omega":
                t_omega_rel, omega_z = arr_t[mask], arr_y[mask]
            else:
                t_current_rel, current = arr_t[mask], arr_y[mask]

    current_filtered = apply_filter(t_current_rel, current, args.filter)

    plot(t_omega_rel, omega_z, t_current_rel, current, current_filtered, args.filter, args.output)


def plot(t_omega, omega_z, t_current, current, current_filtered, filter_mode, output_path):
    fig, ax1 = plt.subplots(figsize=(12, 4.5), dpi=160)

    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("ωz (rad/s)", color="tab:green")
    ax1.plot(t_omega, omega_z, color="tab:green", linewidth=1.5, label="ωz (yaw-derived)")
    ax1.tick_params(axis="y", labelcolor="tab:green")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Current", color="tab:blue")
    ax2.plot(t_current, current, alpha=0.3, color="tab:blue", label="current (raw)")
    if filter_mode != "none":
        ax2.plot(t_current, current_filtered, color="tab:blue", linewidth=2, label=f"current ({filter_mode})")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2)

    plt.title("Angular Velocity and Current")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Saved: {Path(output_path).resolve()}")


if __name__ == "__main__":
    main()
