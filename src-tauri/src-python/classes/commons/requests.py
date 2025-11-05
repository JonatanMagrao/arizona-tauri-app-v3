import requests

def check_health(url, timeout=3, ok_range=range(200, 300)):
    """
    Retorna:
      reachable: conseguiu resposta HTTP?
      healthy: status em ok_range?
      status: código HTTP ou None
    404 = ngrok and server off
    400 = ngrok on, server off
    500 = server error, verify error on server side
    200 = ngrok and server on
    """
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400 or r.status_code < 200:
            r = requests.get(url, timeout=timeout, allow_redirects=True)
        reachable = True
        healthy = r.status_code in ok_range
        return reachable, healthy, r.status_code
    except requests.RequestException:
        return False, False, None