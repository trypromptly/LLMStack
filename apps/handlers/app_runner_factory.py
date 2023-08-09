class AppRunerFactory:
    @staticmethod
    def get_app_runner(app_type_slug):
        if app_type_slug == 'slack':
            from apps.handlers.slack_app import SlackAppRunner
            return SlackAppRunner
        elif app_type_slug == 'discord':
            from apps.handlers.discord_app import DiscordBotRunner
            return DiscordBotRunner
        elif app_type_slug == 'web':
            from apps.handlers.web_app import WebAppRunner
            return WebAppRunner
        elif app_type_slug == 'text-chat':
            from apps.handlers.chat_app import ChatAppRunner
            return ChatAppRunner
        raise Exception('App type not found')
