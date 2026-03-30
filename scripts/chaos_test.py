import argparse
import subprocess
import time


COMPOSE_FILE = "deploy/docker/docker-compose.yml"


def run(cmd: list[str]) -> None:
    print("[chaos]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def chaos_restart(service: str, downtime_seconds: int) -> None:
    run(["docker", "compose", "-f", COMPOSE_FILE, "stop", service])
    print(f"[chaos] waiting {downtime_seconds}s with {service} stopped")
    time.sleep(downtime_seconds)
    run(["docker", "compose", "-f", COMPOSE_FILE, "start", service])
    run(["docker", "compose", "-f", COMPOSE_FILE, "ps"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chaos test by restarting a container during active workflows")
    parser.add_argument("--service", default="airflow", help="compose service to restart, e.g. airflow or api")
    parser.add_argument("--downtime", type=int, default=20, help="downtime in seconds")
    args = parser.parse_args()

    chaos_restart(service=args.service, downtime_seconds=args.downtime)
    print("[chaos] completed. Validate Airflow retries, task recovery, and alerting behavior.")
