import os
import subprocess
import sys


def main() -> None:
    print("Waiting for database...")
    subprocess.run([sys.executable, "/app/wait_for_db.py"], check=True)

    print("Running migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)

    port = os.environ.get("PORT", "8000")
    print(f"Starting server on port {port}...")
    os.execvp(
        "uvicorn",
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
    )


if __name__ == "__main__":
    main()
