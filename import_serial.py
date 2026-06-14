import serial, csv, time

arduino_port = "/dev/cu.usbserial-1120"
baud_rate = 115200
filename = "arduino_data_1302.csv"

with serial.Serial(arduino_port, baud_rate, timeout=1) as ser, \
     open(filename, "w", newline="") as f:
    writer = csv.writer(f)

    # Wait for Arduino reset and first lines
    time.sleep(2)

    while True:
        try:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if not line:
                continue

            # Skip any non-CSV lines (e.g., error messages)
            if "," not in line:
                print("SKIP:", line)
                continue

            row = line.split(",")
            print(row)
            writer.writerow(row)
            f.flush()
        except KeyboardInterrupt:
            break