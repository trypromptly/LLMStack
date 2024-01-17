import os
import platform
import secrets
import subprocess
import sys
from collections import defaultdict
import argparse
import docker
import toml


def run_django_command(command: list[str] = ["manage.py", "runserver"]):
    """Run a Django command"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llmstack.server.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(command)


def prepare_env():
    """
    Verifies that .llmstack dir exists in current directory or user's home dir.
    If it doesn't exist, creates it and returns the .env.local file path.
    """
    if not os.path.exists(".llmstack") and not os.path.exists(
        os.path.join(os.path.expanduser("~"), ".llmstack"),
    ):
        # Create .llmstack dir in user's home dir
        os.mkdir(os.path.join(os.path.expanduser("~"), ".llmstack"))

    if not os.path.exists(".llmstack/config") and not os.path.exists(
        os.path.join(os.path.expanduser("~"), ".llmstack/config"),
    ):
        # Copy config.toml file from installed package to ~/.llmstack/config
        import shutil

        shutil.copyfile(
            os.path.join(
                os.path.dirname(__file__),
                "config.toml",
            ),
            os.path.join(
                os.path.expanduser("~"),
                ".llmstack",
                "config",
            ),
        )

        # Given this is the first time the user is running llmstack, we should
        # ask the user for secret key, cipher_key_salt, database_password and
        # save it in the config file
        config_path = os.path.join(
            os.path.expanduser("~"),
            ".llmstack",
            "config",
        )
        config = {}
        with open(config_path) as f:
            config = toml.load(f)
            config["llmstack"]["secret_key"] = secrets.token_urlsafe(32)
            config["llmstack"]["cipher_key_salt"] = secrets.token_urlsafe(32)
            config["llmstack"]["database_password"] = secrets.token_urlsafe(32)
            # Ask the user for admin username, email and password
            sys.stdout.write(
                "It looks like you are running LLMStack for the first time. Please provide the following information:\n\n",
            )

            config["llmstack"]["admin_username"] = (
                input(
                    "Enter admin username: (default: admin) ",
                )
                or "admin"
            )
            config["llmstack"]["admin_email"] = (
                input(
                    "Enter admin email: ",
                )
                or ""
            )
            config["llmstack"]["admin_password"] = (
                input(
                    "Enter admin password: (default: promptly) ",
                )
                or "promptly"
            )
            config["llmstack"]["default_openai_api_key"] = (
                input(
                    "Enter default OpenAI API key: (Leave empty to configure in settings later) ",
                )
                or ""
            )

        with open(config_path, "w") as f:
            toml.dump(config, f)

    # Chdir to .llmstack
    if not os.path.exists(".llmstack") and os.path.exists(
        os.path.join(os.path.expanduser("~"), ".llmstack"),
    ):
        os.chdir(os.path.join(os.path.expanduser("~"), ".llmstack"))
    elif os.path.exists(".llmstack"):
        os.chdir(".llmstack")

    # Throw error if config file doesn't exist
    if not os.path.exists("config"):
        sys.exit(
            "ERROR: config file not found. Please create one in ~/.llmstack/config",
        )

    # Updates to config.toml
    config_path = os.path.join("config")
    config = {}
    with open(config_path) as f:
        config = toml.load(f)

        if "generatedfiles_root" not in config:
            config["generatedfiles_root"] = "./generatedfiles"

        if "use_remote_job_queue" not in config:
            config["use_remote_job_queue"] = True

        if "llmstack-runner" not in config:
            config["llmstack-runner"] = {}

        if "host" not in config["llmstack-runner"]:
            config["llmstack-runner"]["host"] = "localhost"

        if "port" not in config["llmstack-runner"]:
            config["llmstack-runner"]["port"] = 50051

        if "wss_port" not in config["llmstack-runner"]:
            config["llmstack-runner"]["wss_port"] = 50052

        if "playwright_port" not in config["llmstack-runner"]:
            config["llmstack-runner"]["playwright_port"] = 50053

        if "rq_redis_port" not in config["llmstack-runner"]:
            config["llmstack-runner"]["rq_redis_port"] = 50379

        if "rq_redis_host" not in config["llmstack-runner"]:
            config["llmstack-runner"]["rq_redis_host"] = "localhost"

    with open(config_path, "w") as f:
        toml.dump(config, f)

    return config_path


def start_runner(environment):
    """Start llmstack-runner container"""
    print("[llmstack-runner] Starting LLMStack Runner")
    client = docker.from_env()
    runner_container = None
    image_name = environment.get(
        "RUNNER_IMAGE_NAME",
        "ghcr.io/trypromptly/llmstack-runner",
    )
    image_tag = environment.get("RUNNER_IMAGE_TAG", "main")

    # Pull image if it is not locally available
    if not any(f"{image_name}:{image_tag}" in image.tags for image in client.images.list()):
        print(f"[llmstack-runner] Pulling {image_name}:{image_tag}")

        layers_status = defaultdict(dict)
        response = client.api.pull(
            image_name,
            tag=image_tag,
            stream=True,
            decode=True,
        )
        for line in response:
            if "id" in line:
                layer_id = line["id"]
                # Update the status of this layer
                layers_status[layer_id].update(line)

                # Print the current status of all layers
                for layer, status in layers_status.items():
                    print(
                        f"[llmstack-runner] Layer {layer}: {status.get('status', '')} {status.get('progress', '')}",
                    )
                print()  # Add a blank line for better readability

            elif "status" in line and "id" not in line:
                # Global status messages without a specific layer ID
                print(line["status"])

            elif "error" in line:
                print(f"Error: {line['error']}")
                break

    try:
        runner_container = client.containers.get("llmstack-runner")
    except docker.errors.NotFound:
        runner_container = client.containers.run(
            f"{image_name}:{image_tag}",
            name="llmstack-runner",
            ports={
                "50051/tcp": os.environ["RUNNER_PORT"],
                "50052/tcp": os.environ["RUNNER_WSS_PORT"],
                "50053/tcp": os.environ["RUNNER_PLAYWRIGHT_PORT"],
                "6379/tcp": os.environ["RUNNER_RQ_REDIS_PORT"],
            },
            detach=True,
            remove=True,
            environment=environment,
        )

    # Start runner container if not already running
    print("[llmstack-runner] Started LLMStack Runner")
    if runner_container.status != "running":
        runner_container.start()

    # Stream logs starting from the end to stdout
    for line in runner_container.logs(stream=True, follow=True):
        print(f'[llmstack-runner] {line.decode("utf-8").strip()}')


def stop_runner():
    """Stop llmstack-runner container"""
    print("\nStopping LLMStack Runner\n")
    client = docker.from_env()
    runner_container = None
    try:
        runner_container = client.containers.get("llmstack-runner")
    except docker.errors.NotFound:
        pass

    if runner_container:
        runner_container.stop()

    client.close()


def main():
    """Main entry point for the application script"""

    def signal_handler(sig, frame):
        stop_runner()
        if runner_thread.is_alive():
            runner_thread.join()
        if server_process.poll() is None:  # Check if the process is still running
            server_process.terminate()
            server_process.wait()
        sys.exit(0)

    # Get config file path
    env_path = prepare_env()

    # Setup CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", default=None)

    # Load environment variables from config under [llmstack] section
    llmstack_environment = {}
    runner_environment = {}
    with open(env_path) as f:
        config = toml.load(f)
        for key in config["llmstack"]:
            os.environ[key.upper()] = str(config["llmstack"][key])
            llmstack_environment[key.upper()] = str(config["llmstack"][key])
        for key in config["llmstack-runner"]:
            os.environ[f"RUNNER_{key.upper()}"] = str(
                config["llmstack-runner"][key],
            )
            runner_environment[f"RUNNER_{key.upper()}"] = str(
                config["llmstack-runner"][key],
            )

    # Load CLI args
    args = parser.parse_args()
    if args.port is not None:
        os.environ["LLMSTACK_PORT"] = args.port
    if args.host is not None:
        os.environ["HOST"] = args.host

    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        print("Starting LLMStack")
        run_server_command = [
            "manage.py",
            "runserver",
            os.environ["LLMSTACK_PORT"],
        ]
        if "windows" in platform.platform().lower():
            run_server_command.append("--noreload")
        run_django_command(
            run_server_command,
        )
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "manage.py":
        run_django_command(sys.argv[1:])
        sys.exit(0)

    run_django_command(["manage.py", "migrate", "--noinput"])
    run_django_command(
        [
            "manage.py",
            "loaddata",
            os.path.join(
                os.path.dirname(__file__),
                "fixtures/initial_data.json",
            ),
        ],
    )
    run_django_command(["manage.py", "createcachetable"])
    run_django_command(["manage.py", "clearcache"])

    # Install default playwright browsers
    subprocess.run(["playwright", "install", "chromium"])

    # Start llmstack-runner container in a separate thread
    import threading

    runner_thread = threading.Thread(
        target=start_runner,
        args=([runner_environment]),
    )
    runner_thread.start()

    # Run llmstack runserver in a separate process
    server_process = subprocess.Popen(["llmstack", "runserver"])

    # Run llmstack rqworker in a separate process
    print("Starting LLMStack rqworker")
    rqworker_process = subprocess.Popen(
        ["llmstack", "manage.py", "rqworker", "default", "--verbosity=0", "--with-scheduler"],
    )

    # Wait for server to be up at LLMSTACK_PORT and open browser
    import time
    import webbrowser

    while True:
        try:
            import requests

            requests.get(
                f'http://localhost:{os.environ["LLMSTACK_PORT"]}',
            )
            break
        except Exception:
            print(
                "Waiting for LLMStack server to be up...",
            )
            time.sleep(1)

    webbrowser.open(f'http://localhost:{os.environ["LLMSTACK_PORT"]}')

    # Wait for signal to stop
    import signal

    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    # Block the main thread until a signal is received
    if "windows" in platform.platform().lower():
        os.system("pause")
    else:
        signal.pause()

    # Stop runner container
    stop_runner()
    runner_thread.join()

    # Stop server process
    server_process.terminate()
    server_process.wait()

    # Stop rqworker process
    rqworker_process.terminate()
    rqworker_process.wait()


if __name__ == "__main__":
    main()
