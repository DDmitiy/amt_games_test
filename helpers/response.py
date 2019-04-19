from aiohttp.web_response import Response, json_response


def json_error_400(msg: str) -> Response:
    return json_response({'error': msg}, status=400)


def json_internal_error() -> Response:
    return json_response({'error': 'internal_server'}, status=500)
