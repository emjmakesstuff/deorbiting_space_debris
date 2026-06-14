# Deorbiting Space Debris — Experiment Tools

## Dependencies

```
pip install pyserial numpy matplotlib
```

## Running Experiments

```
python run_experiments.py <data_directory>
```

Commands:
- `start` — begin a new trial (creates `trial_N/` folder with timestamped CSV)
- `stop` — stop the current trial
- Any other text in idle state — saved as notes to `Notes.txt`
- `Ctrl-C` — exit

Each trial folder contains:
- `arduino_data_YYYYMMDD_HHMMSS.csv` — current readings with epoch timestamps (ms)
- `Notes.txt` — start/stop timestamps and any notes

## Testing with Mock Arduino

The mock creates a virtual serial port that outputs fake current data, so you can test without hardware.

**Terminal 1** — start the mock:
```
python mock_arduino.py
```
It will print a device path like `Mock Arduino on: /dev/ttys005`. Copy this path.

**Terminal 2** — run the orchestrator with `--mock`:
```
python run_experiments.py ./test_data --mock /dev/ttys005
```

You can also run `import_serial.py` directly against the mock:
```
python import_serial.py output.csv --mock /dev/ttys005
```

## Plotting

```
python plot_csv.py <csv_file> [--t-start 5] [--t-end 30] [--filter moving_average|lowpass_1pole|none]
```

## ROS Bag Data

Extract pose data from a ROS 2 bag:
```
python load_rosbag.py <file.db3>              # preview
python load_rosbag.py <file.db3> -o poses.csv  # export to CSV
```
