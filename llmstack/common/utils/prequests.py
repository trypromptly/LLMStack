import json
import requests
from urllib.parse import urlparse


def request(method, url, **kwargs):
    _connection = kwargs.pop('_connection', None)
    if _connection:
        connection = _connection
        # connection is one of api_key, basic_auth, bearer_token, oauth2 or web_login 
        if connection.get('base_connection_type', None) == 'credentials':
            if connection.get('connection_type_slug', None) == 'basic_authentication':
                kwargs['auth'] = (connection['username'], connection['password'])
            elif connection.get('connection_type_slug', None) == 'bearer_authentication':
                assert 'Authorization' not in kwargs['headers']
                token = connection.get('configuration', {}).get('token', None)
                kwargs['headers'] = {**kwargs['headers'], **{'Authorization': 'Bearer ' + token}}
            elif connection.get('connection_type_slug', None) == 'api_key_authentication':
                header_key = connection.get('configuration', {}).get('header_key', None)
                api_key = connection.get('configuration', {}).get('api_key', None)
                kwargs['headers'] = {**kwargs['headers'], **{header_key: api_key}}
                
        elif  connection.get('base_connection_type', None) == 'oauth2':
            assert 'Authorization' not in kwargs['headers']
            token = connection.get('configuration', {}).get('token', None)
            kwargs['headers'] = {**kwargs['headers'], **{'Authorization': 'Bearer ' + token}}
        
        elif connection.get('base_connection_type', None) == 'browser_login' and connection.get('connection_type_slug', None) == 'web_login':
            _storage_state = json.loads(connection.get('configuration', {}).get('_storage_state', '{}'))
            cookie_list = _storage_state.get('cookies', {})
            url_domain = '.'.join(urlparse(url).netloc.split('.')[-2:])
            cookies = {}
            for cookie_entry in cookie_list:
                if cookie_entry.get('domain', None):
                    if cookie_entry['domain'].endswith(url_domain):
                        cookies[cookie_entry['name']] = cookie_entry['value']

            kwargs['cookies'] = {**kwargs.get('cookies', {}), **cookies}
            
    return requests.request(method=method, url=url, **kwargs)

def get(url, params=None, **kwargs):
    r"""Sends a GET request.

    :param url: URL for the new :class:`Request` object.
    :param params: (optional) Dictionary, list of tuples or bytes to send
        in the query string for the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request("get", url, params=params, **kwargs)


def options(url, **kwargs):
    r"""Sends an OPTIONS request.

    :param url: URL for the new :class:`Request` object.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request("options", url, **kwargs)


def head(url, **kwargs):
    r"""Sends a HEAD request.

    :param url: URL for the new :class:`Request` object.
    :param \*\*kwargs: Optional arguments that ``request`` takes. If
        `allow_redirects` is not provided, it will be set to `False` (as
        opposed to the default :meth:`request` behavior).
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    kwargs.setdefault("allow_redirects", False)
    return request("head", url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    r"""Sends a POST request.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request("post", url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    r"""Sends a PUT request.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request("put", url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    r"""Sends a PATCH request.

    :param url: URL for the new :class:`Request` object.
    :param data: (optional) Dictionary, list of tuples, bytes, or file-like
        object to send in the body of the :class:`Request`.
    :param json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request("patch", url, data=data, **kwargs)


def delete(url, **kwargs):
    r"""Sends a DELETE request.

    :param url: URL for the new :class:`Request` object.
    :param \*\*kwargs: Optional arguments that ``request`` takes.
    :return: :class:`Response <Response>` object
    :rtype: requests.Response
    """

    return request("delete", url, **kwargs)
