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
        # Create .llmstack dir in user's home dir
        os.mkdir(os.path.join(os.path.expanduser('~'), '.llmstack'))

    if not os.path.exists('.llmstack/config') and not os.path.exists(os.path.join(os.path.expanduser('~'), '.llmstack/config')):
        # Copy config.toml file from installed package to ~/.llmstack/config
        import shutil
        shutil.copyfile(os.path.join(os.path.dirname(__file__), 'config.toml'), os.path.join(
            os.path.expanduser('~'), '.llmstack', 'config'))

        # Given this is the first time the user is running llmstack, we should
        # ask the user for secret key, cipher_key_salt, database_password and save it in the config file
        import toml
        import secrets
        config_path = os.path.join(
            os.path.expanduser('~'), '.llmstack', 'config')
        config = {}
        with open(config_path) as f:
            config = toml.load(f)
            config['llmstack']['secret_key'] = secrets.token_urlsafe(32)
            config['llmstack']['cipher_key_salt'] = secrets.token_urlsafe(32)
            config['llmstack']['database_password'] = secrets.token_urlsafe(32)
            # Ask the user for admin username, email and password
            sys.stdout.write(
                'It looks like you are running LLMStack for the first time. Please provide the following information:\n\n')

            config['llmstack']['admin_username'] = input(
                'Enter admin username: (default: admin)') or 'admin'
            config['llmstack']['admin_email'] = input(
                'Enter admin email: ') or ''
            config['llmstack']['admin_password'] = input(
                'Enter admin password: (default: promptly) ') or 'promptly'
            config['llmstack']['default_openai_api_key'] = input(
                'Enter default OpenAI API key: (Leave empty to configure in settings later) ') or ''
        with open(config_path, 'w') as f:
            toml.dump(config, f)

    # Chdir to .llmstack
    if not os.path.exists('.llmstack') and os.path.exists(os.path.join(os.path.expanduser('~'), '.llmstack')):
        os.chdir(os.path.join(os.path.expanduser('~'), '.llmstack'))
    elif os.path.exists('.llmstack'):
        os.chdir('.llmstack')

    # Throw error if config file doesn't exist
    if not os.path.exists('config'):
        sys.exit(
            'ERROR: config file not found. Please create one in ~/.llmstack/config')

    return os.path.join('config')


def main():
    """Main entry point for the application script"""

    # Get config file path
    env_path = prepare_env()

    # Load environment variables from config under [llmstack] section
    import toml
    with open(env_path) as f:
        config = toml.load(f)
        for key in config['llmstack']:
            os.environ[key.upper()] = str(config['llmstack'][key])

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

    # Install default playwright browsers
    import subprocess
    subprocess.run(['playwright', 'install', 'chromium'])

    # Run llmstack runserver in a separate process
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
