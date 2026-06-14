import argparse, struct, sqlite3, csv


POSE_OFFSET = 28


def get_epoch_time_ms(timestamp_ns):
    return int(timestamp_ns // 1_000_000)


def parse_pose_stamped(data):
    px, py, pz, ox, oy, oz, ow = struct.unpack_from("<7d", data, POSE_OFFSET)
    return px, py, pz, ox, oy, oz, ow


def load_rosbag(db3_path):
    con = sqlite3.connect(db3_path)
    cur = con.cursor()
    cur.execute("SELECT timestamp, data FROM messages ORDER BY timestamp")

    rows = []
    for timestamp_ns, data in cur:
        px, py, pz, ox, oy, oz, ow = parse_pose_stamped(data)
        rows.append({
            "epoch_ms": get_epoch_time_ms(timestamp_ns),
            "x": px, "y": py, "z": pz,
            "ox": ox, "oy": oy, "oz": oz, "ow": ow,
        })

    con.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description="Extract pose data from a ROS 2 bag (.db3)")
    parser.add_argument("db3_file", help="Path to the .db3 file")
    parser.add_argument("-o", "--output", help="Output CSV path (default: print to stdout)")
    args = parser.parse_args()

    rows = load_rosbag(args.db3_file)

    fields = ["epoch_ms", "x", "y", "z", "ox", "oy", "oz", "ow"]

    if args.output:
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows to {args.output}")
    else:
        for r in rows[:10]:
            print(r)
        if len(rows) > 10:
            print(f"... ({len(rows)} total rows)")


if __name__ == "__main__":
    main()
