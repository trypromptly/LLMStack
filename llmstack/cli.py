import argparse
import os
import platform
import random
import re
import secrets
import signal
import sys
import tempfile
import time
import webbrowser

import requests
import toml
from python_on_whales import DockerClient


def prepare_env():
    """
    Verifies that .llmstack dir exists in current directory or user's home dir.
    If it doesn't exist, creates it and returns the file path.
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
            keep_updated = (
                input(
                    "Would you like to receive updates about LLMStack? (Y/n) ",
                )
                or "Y"
            )

            if keep_updated.lower() != "n":
                # Add the user to the mailing list
                try:
                    webbrowser.open("https://forms.gle/UKQ9rumczFDvwVmg7")
                except Exception:
                    print("Failed to open browser. Please open the browser and navigate to the URL below.")
                    print("https://forms.gle/UKQ9rumczFDvwVmg7")

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

    with open(config_path, "w") as f:
        toml.dump(config, f)

    # Change permissions of config file
    os.chmod(config_path, 0o600)

    return config_path


def stop(exit_code=0):
    """Stop LLMStack server"""
    print("Stopping LLMStack server...")
    docker_client = DockerClient(
        compose_project_name="llmstack",
    )
    docker_client.compose.down()
    sys.exit(exit_code)


def wait_for_server(llmstack_environment, timeout):
    """Wait for server to be up and open browser"""

    start_time = time.time()
    while True:
        try:
            print(
                "\nWaiting for LLMStack server to be up...",
                end="",
            )
            resp = requests.get(
                f'http://{llmstack_environment["LLMSTACK_HOST"]}:{llmstack_environment["LLMSTACK_PORT"]}',
            )
            if resp.status_code < 400:
                break

            time.sleep(2 + (random.randint(0, 1000) / 1000))

            # If we have waited for more than 3 minutes, exit
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout waiting for LLMStack server to be up.")
        except TimeoutError:
            print(
                "\nFailed to connect to LLMStack server. Exiting...",
            )
            print_compose_logs(follow=False)
            stop(1)
        except Exception:
            time.sleep(2 + (random.randint(0, 1000) / 1000))
            continue

    try:
        webbrowser.open(f'http://{llmstack_environment["LLMSTACK_HOST"]}:{llmstack_environment["LLMSTACK_PORT"]}')
    except Exception:
        print("\nFailed to open browser. Please open the browser and navigate to the URL below.")
        print(
            f"LLMStack server is running at http://{llmstack_environment['LLMSTACK_HOST']}:{llmstack_environment['LLMSTACK_PORT']}"
        )


def print_compose_logs(follow=True, stream=True):
    """Get logs for LLMStack server"""
    docker_client = DockerClient(
        compose_project_name="llmstack",
    )

    if not docker_client.compose.ps():
        print("LLMStack server is not running.")
        sys.exit(0)

    logs = docker_client.compose.logs(follow=follow, stream=stream)
    for _, line in logs:
        print(line.decode("utf-8").strip())


def start(llmstack_environment):
    # Create a temp file with this environment variables to be used by docker-compose
    with tempfile.NamedTemporaryFile(mode="w") as f:
        for key in llmstack_environment:
            f.write(f"{key}={llmstack_environment[key]}\n")
        f.flush()

        # Start the containers
        docker_client = DockerClient(
            compose_files=[os.path.join(os.path.dirname(__file__), "docker-compose.yml")],
            compose_env_file=f.name,
        )

        # Start the containers
        docker_logs = docker_client.compose.up(detach=True, stream_logs=True, pull="missing")

        compose_output = []
        last_output_len = 0
        for _, line in docker_logs:
            output = line.decode("utf-8").strip()

            # If the output has a hash "26f9b446db9e Extracting  450.1MB/523.6M", replace in compose output
            if len(output.split(" ")) > 1:
                output_part = output.split(" ")[0]
                if len(output_part) == 12 and re.fullmatch(r"[0-9a-f]+", output_part):
                    for i, compose_output_part in enumerate(compose_output):
                        if output_part in compose_output_part:
                            compose_output.pop(i)
                            compose_output.append(output)

            # If the output is not already in compose_output, add it
            if output not in compose_output:
                compose_output.append(output)

            # Clear the previous output
            for _ in range(last_output_len - 1):
                print("\033[F\033[K", end="")

            print("\n".join(compose_output[-10:]), end="", flush=True)
            last_output_len = len(compose_output[-10:])


def main():
    """Main entry point for the application script"""

    def signal_handler(sig, frame):
        stop()

    # Get config file path
    env_path = prepare_env()

    # Setup CLI args
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--host", default=None, help="Host to bind to. Defaults to localhost.")
    parent_parser.add_argument("--port", default=None, help="Port to bind to. Defaults to 3000.")
    parent_parser.add_argument("--quiet", default=False, action="store_true", help="Suppress output.")
    parent_parser.add_argument("--no-browser", default=False, action="store_true", help="Do not open browser.")
    parent_parser.add_argument("--detach", default=False, action="store_true", help="Run in detached mode.")
    parent_parser.add_argument("--timeout", default=180, help=argparse.SUPPRESS)
    parent_parser.add_argument(
        "--registry",
        default="ghcr.io/trypromptly/",
        help=argparse.SUPPRESS,
    )
    parent_parser.add_argument("--tag", help=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(
        description="LLMStack: No-code platform to build AI agents", parents=[parent_parser]
    )
    subparsers = parser.add_subparsers(title="commands", help="Available commands", dest="command")

    subparsers.add_parser("start", help="Start LLMStack server", parents=[parent_parser])
    subparsers.add_parser("stop", help="Stop LLMStack server")
    subparsers.add_parser("logs", help="Get logs for LLMStack server")

    # Load CLI args
    args = parser.parse_args()

    # Load environment variables from config under [llmstack] section
    llmstack_environment = {}
    with open(env_path) as f:
        config = toml.load(f)
        for key in config["llmstack"]:
            os.environ[key.upper()] = str(config["llmstack"][key])
            llmstack_environment[key.upper()] = str(config["llmstack"][key])

    if args.command == "stop":
        stop()
        return

    # Start the containers
    if not args.command or args.command == "start":
        if args.host is not None:
            llmstack_environment["LLMSTACK_HOST"] = args.host

        if args.port is not None:
            llmstack_environment["LLMSTACK_PORT"] = args.port
            os.environ["LLMSTACK_PORT"] = args.port

        protocol = "http"

        llmstack_environment[
            "SITE_URL"
        ] = f'{protocol}://{llmstack_environment["LLMSTACK_HOST"]}:{llmstack_environment["LLMSTACK_PORT"]}'

        # Set registry and tag
        llmstack_environment["REGISTRY"] = args.registry

        if args.tag:
            llmstack_environment["TAG"] = args.tag

        # Load default store apps
        os.environ["DJANGO_MANAGEPY_LOADSTOREAPPS"] = "on"

        start(llmstack_environment)

        # Wait for server to be up and open browser
        if not args.no_browser:
            wait_for_server(llmstack_environment, args.timeout)

        print(f"\n\nLLMStack server is running at {llmstack_environment['SITE_URL']}.")

        # If running in detached mode, return
        if args.detach:
            print("Running in detached mode. Use `llmstack stop` to stop the server.")
            return

        print("Press Ctrl+C to stop the server.")

    # Register the signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)

    if not args.quiet or args.command == "logs":
        print_compose_logs()

    # Block the main thread until a signal is received
    if "windows" in platform.platform().lower():
        os.system("pause")
    else:
        signal.pause()

    # Stop the containers
    stop()


if __name__ == "__main__":
    main()
