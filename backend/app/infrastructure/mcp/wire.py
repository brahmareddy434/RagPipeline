"""Transparent stdio tee. Preserve actual JSON-RPC lines, never synthesize messages.

Only enabled explicitly for local fictional demo servers. Logs include tool data.
"""
import argparse
import json
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr.buffer)

    def pump(source, destination, direction):
        try:
            for raw in iter(source.readline, b""):
                # Log before forwarding: response ordering follows the observed request.
                with lock, path.open("a", encoding="utf-8") as log:
                    log.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                          "direction": direction, "raw": raw.decode("utf-8")}) + "\n")
                destination.write(raw)
                destination.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            if direction == "client->server":
                destination.close()

    incoming = threading.Thread(target=pump, args=(sys.stdin.buffer, child.stdin, "client->server"), daemon=True)
    incoming.start()
    try:
        pump(child.stdout, sys.stdout.buffer, "server->client")
        child.wait(timeout=5)
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=5)


if __name__ == "__main__":
    main()
