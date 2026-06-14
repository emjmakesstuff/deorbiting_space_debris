import argparse, serial, csv, time


def get_epoch_time_ms():
    return int(time.time() * 1000)


def open_serial(port, baud_rate, mock=False):
    kwargs = {"port": port, "baudrate": baud_rate, "timeout": 1}
    if mock:
        kwargs["dsrdtr"] = False
        kwargs["rtscts"] = False
    ser = serial.Serial(**kwargs)
    if not mock:
        time.sleep(2)
    return ser


def main():
    parser = argparse.ArgumentParser(description="Record serial data from Arduino to CSV")
    parser.add_argument("filename", nargs="?", default="arduino_data.csv", help="Output CSV path")
    parser.add_argument("--mock", metavar="DEVICE", help="Use a mock Arduino at the given device path")
    args = parser.parse_args()

    port = args.mock if args.mock else "/dev/cu.usbserial-1120"

    with open_serial(port, 115200, mock=bool(args.mock)) as ser, \
         open(args.filename, "w", newline="") as f:
        writer = csv.writer(f)
        count = 0
        last_report = time.time()

        while True:
            try:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                try:
                    float(line.split(",")[0])
                except ValueError:
                    continue

                row = line.split(",")
                row.append(str(get_epoch_time_ms()))
                writer.writerow(row)
                f.flush()
                count += 1

                now = time.time()
                if now - last_report >= 1.0:
                    print(f"{count} data points collected")
                    last_report = now
            except KeyboardInterrupt:
                print(f"\nDone. {count} total data points.")
                break


if __name__ == "__main__":
    main()
