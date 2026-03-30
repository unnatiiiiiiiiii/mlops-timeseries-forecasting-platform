import subprocess


def build_rollout_commands(decision: str, namespace: str = "default") -> list[list[str]]:
    if decision == "promote":
        return [
            [
                "kubectl",
                "-n",
                namespace,
                "scale",
                "deployment/forecasting-api-stable",
                "--replicas=3",
            ],
            [
                "kubectl",
                "-n",
                namespace,
                "scale",
                "deployment/forecasting-api-canary",
                "--replicas=0",
            ],
        ]

    if decision == "rollback":
        return [
            [
                "kubectl",
                "-n",
                namespace,
                "scale",
                "deployment/forecasting-api-canary",
                "--replicas=0",
            ]
        ]

    return []


def execute_rollout(commands: list[list[str]]) -> list[dict]:
    results = []
    for cmd in commands:
        process = subprocess.run(cmd, capture_output=True, text=True, check=False)
        results.append(
            {
                "command": " ".join(cmd),
                "returncode": process.returncode,
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip(),
            }
        )
    return results
