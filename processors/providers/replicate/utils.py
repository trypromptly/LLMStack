import requests


def fetch_data_from_api(url, param_values, headers):
    try:
        result = requests.post(url, json=param_values, headers=headers)
    except:
        pass
    return result
