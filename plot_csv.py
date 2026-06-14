import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- settings ----------
path = Path("arduino_data_1257.csv")   # your file
dt = 0.010                # seconds/sample (delay(10))
t_start = 30             # trim: start time (s)
t_end   = None            # trim: end time (s) or None

# Filtering (pick one)
filter_mode = "moving_average"   # "none" | "moving_average" | "lowpass_1pole"
ma_window_s = 0.20               # moving average window (s)

lowpass_fc = 5.0                 # Hz, for 1-pole lowpass
# ------------------------------

# read (robust: ignores blank lines, uses first field before any comma)
y = []
with path.open() as f:
    for line in f:
        s = line.strip()
        if not s:
            continue
        s = s.split(",")[0].strip()
        y.append(float(s))

y = np.array(y, float)
t = np.arange(len(y)) * dt

# trim by time
i0 = int(round(t_start / dt))
i1 = len(y) if t_end is None else int(round(t_end / dt))
t = t[i0:i1] - t[i0]
y = y[i0:i1]

# filter
y_f = y.copy()
if filter_mode == "moving_average":
    w = max(1, int(round(ma_window_s / dt)))
    kernel = np.ones(w) / w
    y_f = np.convolve(y, kernel, mode="same")
elif filter_mode == "lowpass_1pole":
    alpha = (2*np.pi*lowpass_fc*dt) / (1 + 2*np.pi*lowpass_fc*dt)  # stable form
    y_f = np.empty_like(y)
    y_f[0] = y[0]
    for n in range(1, len(y)):
        y_f[n] = y_f[n-1] + alpha*(y[n] - y_f[n-1])
elif filter_mode == "none":
    pass
else:
    raise ValueError("filter_mode must be: none, moving_average, lowpass_1pole")

# plot
plt.figure()
plt.plot(t, y, label="raw", alpha=0.5)
plt.plot(t, y_f, label=f"filtered ({filter_mode})", linewidth=2)
plt.grid(True)
plt.xlabel("Time (s)")
plt.ylabel("Current")
plt.legend()
plt.tight_layout()
plt.show()