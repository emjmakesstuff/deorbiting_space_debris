import argparse, subprocess, sys, signal, time
from pathlib import Path
from datetime import datetime


def get_epoch_time_ms():
    return int(time.time() * 1000)


def write_notes(trial_dir, start_epoch, stop_epoch, notes):
    with open(trial_dir / "Notes.txt", "w") as f:
        start_fmt = datetime.fromtimestamp(start_epoch / 1000).strftime("%Y%m%d %H:%M:%S")
        stop_fmt = datetime.fromtimestamp(stop_epoch / 1000).strftime("%Y%m%d %H:%M:%S")
        f.write(f"Start: {start_epoch} ({start_fmt})\n")
        f.write(f"Stop:  {stop_epoch} ({stop_fmt})\n")
        if notes:
            f.write(f"\nNotes:\n")
            for note in notes:
                f.write(f"  {note}\n")


def main():
    parser = argparse.ArgumentParser(description="Run multiple experiment trials")
    parser.add_argument("data_dir", help="Directory to store trial data")
    parser.add_argument("--mock", metavar="DEVICE", help="Use a mock Arduino at the given device path")
    args = parser.parse_args()

    base_dir = Path(args.data_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    trial_num = 0
    process = None
    current_trial_dir = None
    start_epoch = None
    stop_epoch = None
    notes = []

    print(f"Data directory: {base_dir.resolve()}")
    print("Type 'start' to begin a trial.")

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            if process and process.poll() is None:
                process.send_signal(signal.SIGINT)
                process.wait()
            print("\nExiting.")
            break

        if not cmd:
            continue

        if process and process.poll() is None:
            if cmd == "stop":
                process.send_signal(signal.SIGINT)
                process.wait()
                process = None
                stop_epoch = get_epoch_time_ms()
                write_notes(current_trial_dir, start_epoch, stop_epoch, notes)
                print(f"Trial {trial_num} stopped.")
                print("Type notes for this trial, 'start' for next trial, or Ctrl-C to quit.")
            else:
                print("Recording in progress. Type 'stop' to end the current trial.")
            continue

        if cmd == "start":
            trial_num += 1
            current_trial_dir = base_dir / f"trial_{trial_num}"
            current_trial_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"arduino_data_{timestamp}.csv"
            csv_path = current_trial_dir / csv_filename

            start_epoch = get_epoch_time_ms()
            notes = []
            print(f"Starting trial {trial_num}: {csv_path}")

            script_dir = Path(__file__).parent
            cmd_args = [sys.executable, str(script_dir / "import_serial.py"), str(csv_path)]
            if args.mock:
                cmd_args += ["--mock", args.mock]
            process = subprocess.Popen(cmd_args)
        else:
            if current_trial_dir:
                notes.append(cmd)
                write_notes(current_trial_dir, start_epoch, stop_epoch, notes)
                print("Note saved.")
            else:
                print("No trial yet. Type 'start' to begin.")


if __name__ == "__main__":
    main()
