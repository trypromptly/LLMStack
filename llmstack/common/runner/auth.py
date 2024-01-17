import logging
import sys

from websockify.auth_plugins import AuthenticationError

logger = logging.getLogger(__name__)


class BasicHTTPAuthWithRedis:
    """Verifies Basic Auth headers. Specify src as redis host:port:db:password"""

    def __init__(self, src=None):
        try:
            import redis  # noqa
        except ImportError:
            logger.error("Unable to load redis module")
            sys.exit()
        # Default values
        self._port = 6379
        self._db = 0
        self._password = None
        try:
            fields = src.split(":")
            if len(fields) == 1:
                self._server = fields[0]
            elif len(fields) == 2:
                self._server, self._port = fields
                if not self._port:
                    self._port = 6379
            elif len(fields) == 3:
                self._server, self._port, self._db = fields
                if not self._port:
                    self._port = 6379
                if not self._db:
                    self._db = 0
            elif len(fields) == 4:
                self._server, self._port, self._db, self._password = fields
                if not self._port:
                    self._port = 6379
                if not self._db:
                    self._db = 0
                if not self._password:
                    self._password = None
            else:
                raise ValueError
            self._port = int(self._port)
            self._db = int(self._db)
            logger.info(
                "BasicHTTPAuthWithRedis backend initilized (%s:%s)" % (self._server, self._port),
            )
        except ValueError:
            logger.error(
                "The provided --auth-source='%s' is not in the "
                "expected format <host>[:<port>[:<db>[:<password>]]]" % src,
            )
            sys.exit()

    def authenticate(self, headers, target_host, target_port):
        import base64

        auth_header = headers.get("Authorization")
        if auth_header:
            if not auth_header.startswith("Basic "):
                self.auth_error()

            try:
                user_pass_raw = base64.b64decode(auth_header[6:])
            except TypeError:
                self.auth_error()

            try:
                # http://stackoverflow.com/questions/7242316/what-encoding-should-i-use-for-http-basic-authentication
                user_pass_as_text = user_pass_raw.decode("ISO-8859-1")
            except UnicodeDecodeError:
                self.auth_error()

            user_pass = user_pass_as_text.split(":", 1)
            if len(user_pass) != 2:
                self.auth_error()

            if not self.validate_creds(*user_pass):
                self.demand_auth()

        else:
            self.demand_auth()

    def validate_creds(self, username, password):
        try:
            import redis
        except ImportError:
            logger.error(
                "package redis not found, are you sure you've installed them correctly?",
            )
            sys.exit()

        client = redis.Redis(
            host=self._server,
            port=self._port,
            db=self._db,
            password=self._password,
        )
        stuff = client.get(username)

        if stuff and stuff.decode("utf-8").strip() == password:
            return True
        else:
            return False

    def auth_error(self):
        raise AuthenticationError(response_code=403)

    def demand_auth(self):
        raise AuthenticationError(
            response_code=401,
            response_headers={
                "WWW-Authenticate": 'Basic realm="Websockify"',
            },
        )
