import os, pty, time, random

master, slave = pty.openpty()
device = os.ttyname(slave)
print(f"Mock Arduino on: {device}")
print("Ctrl-C to stop.")

time.sleep(0.5)

try:
    while True:
        current = round(random.uniform(0.1, 2.0), 4)
        line = f"{current}\n"
        os.write(master, line.encode())
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nMock Arduino stopped.")
finally:
    os.close(master)
    os.close(slave)
