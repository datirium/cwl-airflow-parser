import jwt
from functools import wraps
from flask import request, Response
from airflow.models import Variable


JWT_BACKEND_PUBLIC_KEY = "jwt_backend_public_key"
JWT_BACKEND_CRYPT_ALGORITHM = "jwt_backend_crypt_algorithm"


client_auth = None


def init_app(app):
    pass


def requires_authentication(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        try:
            json_data = {k: v for k, v in request.get_json(force=True).copy().items() if k != "check_payload"}
            check_payload = jwt.decode(request.get_json(force=True)["check_payload"], Variable.get(JWT_BACKEND_PUBLIC_KEY), algorithms=Variable.get(JWT_BACKEND_CRYPT_ALGORITHM))
            assert (json_data == check_payload)
        except Exception:
            return Response("Failed to decrypt or data is corrupted", 403)
        return function(*args, **kwargs)
    return decorated
