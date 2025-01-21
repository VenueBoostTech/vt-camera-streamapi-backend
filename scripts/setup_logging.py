import os
import shutil
import subprocess
from pathlib import Path

def setup_logging():
    """Setup logging directory structure and permissions"""
    # Create log directories
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create log files if they don't exist
    log_files = [
        "system.log",
        "analytics.log",
        "error.log",
        "camera_status.log"
    ]

    for log_file in log_files:
        log_path = log_dir / log_file
        if not log_path.exists():
            log_path.touch()

    print("Log files created successfully")

    # Set correct permissions for Docker
    subprocess.run(["chmod", "-R", "755", str(log_dir)])
    print("Permissions set successfully")

def start_monitoring():
    """Start the monitoring stack"""
    if not Path("monitoring/docker-compose.yml").exists():
        print("Error: docker-compose.yml not found")
        return False

    try:
        # Start monitoring stack
        subprocess.run(
            ["docker-compose", "-f", "monitoring/docker-compose.yml", "up", "-d"],
            check=True
        )
        print("Monitoring stack started successfully")

        # Print access URLs
        print("\nMonitoring URLs:")
        print("Grafana:    http://localhost:3000")
        print("Prometheus: http://localhost:9090")
        print("Loki:      http://localhost:3100")

        return True
    except subprocess.CalledProcessError as e:
        print(f"Error starting monitoring stack: {e}")
        return False

def check_logs(tail_lines=10):
    """Check recent log entries"""
    log_dir = Path("logs")

    if not log_dir.exists():
        print("Log directory not found")
        return

    for log_file in log_dir.glob("*.log"):
        print(f"\nLast {tail_lines} lines of {log_file.name}:")
        print("-" * 50)

        try:
            with open(log_file, 'r') as f:
                # Get last n lines
                lines = f.readlines()[-tail_lines:]
                for line in lines:
                    print(line.strip())
        except Exception as e:
            print(f"Error reading {log_file.name}: {e}")

def cleanup_old_logs(days=30):
    """Clean up logs older than specified days"""
    from datetime import datetime, timedelta

    log_dir = Path("logs")
    cutoff = datetime.now() - timedelta(days=days)

    for log_file in log_dir.glob("*.log"):
        if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff:
            # Create backup before deletion
            backup_name = f"{log_file.stem}_{log_file.stat().st_mtime}.bak"
            shutil.copy2(log_file, log_dir / backup_name)

            # Truncate original file
            log_file.write_text("")
            print(f"Cleaned {log_file.name}, backup created as {backup_name}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Logging system management")
    parser.add_argument("action", choices=["setup", "start", "check", "cleanup"])
    parser.add_argument("--tail", type=int, default=10, help="Number of lines to show for check")
    parser.add_argument("--days", type=int, default=30, help="Days to keep logs for cleanup")

    args = parser.parse_args()

    if args.action == "setup":
        setup_logging()
    elif args.action == "start":
        start_monitoring()
    elif args.action == "check":
        check_logs(args.tail)
    elif args.action == "cleanup":
        cleanup_old_logs(args.days)