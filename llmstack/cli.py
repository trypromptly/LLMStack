import os
import sys


def run_django_command(command: list[str] = ['manage.py', 'runserver']):
    """Run a Django command"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llmstack.server.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(command)


def prepare_env():
    """
    Verifies that .llmstack dir exists in current directory or user's home dir.
    If it doesn't exist, creates it and returns the .env.local file path.
    """
    if not os.path.exists('.llmstack') and not os.path.exists(os.path.join(os.path.expanduser('~'), '.llmstack')):
        os.mkdir(os.path.join(os.path.expanduser('~'), '.llmstack'))

        # Copy .env.local file from installed package to ~/.llmstack/.env.local
        import shutil
        shutil.copyfile(os.path.join(os.path.dirname(__file__), '.env.local'), os.path.join(
            os.path.expanduser('~'), '.llmstack', '.env.local'))

    # Chdir to .llmstack
    if not os.path.exists('.llmstack') and os.path.exists(os.path.join(os.path.expanduser('~'), '.llmstack')):
        os.chdir(os.path.join(os.path.expanduser('~'), '.llmstack'))
    elif os.path.exists('.llmstack'):
        os.chdir('.llmstack')

    # Throw error if .env.local file doesn't exist
    if not os.path.exists('.env.local'):
        sys.exit(
            'ERROR: .env.local file not found. Please create one in ~/.llmstack/.env.local')

    return os.path.join('.env.local')


def main():
    """Main entry point for the application script"""

    # Get .env.local file path
    env_path = prepare_env()

    # Load environment variables from .env.local file
    from dotenv import load_dotenv
    load_dotenv(env_path)

    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        print('Starting LLMStack')
        run_django_command(
            ['manage.py', 'runserver', os.environ['LLMSTACK_PORT']])
        sys.exit(0)

    run_django_command(['manage.py', 'migrate', '--noinput'])
    run_django_command(['manage.py', 'loaddata', os.path.join(
        os.path.dirname(__file__), 'fixtures/initial_data.json')])
    run_django_command(['manage.py', 'createcachetable'])
    run_django_command(['manage.py', 'clearcache'])

    # Run llmstack runserver in a separate process
    import subprocess
    server_process = subprocess.Popen(['llmstack', 'runserver'])

    # Wait for server to be up at LLMSTACK_PORT and open browser
    import time
    import webbrowser

    while True:
        try:
            import requests
            requests.get(
                f'http://localhost:{os.environ["LLMSTACK_PORT"]}')
            break
        except Exception:
            print(
                f'Waiting for LLMStack server to be up...')
            time.sleep(1)

    webbrowser.open(f'http://localhost:{os.environ["LLMSTACK_PORT"]}')

    # Wait for server process to exit
    server_process.wait()
