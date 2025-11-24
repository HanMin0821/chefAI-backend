import jwt
from datetime import datetime, timedelta
from flask import request, jsonify
from functools import wraps
from models import User


SECRET_KEY = "a4f82bc9f0e6a9c3d4b165c0b8271efc"
ALGORITHM = "HS256"


class ApiResponse:
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        return jsonify({
            "success": True,
            "message": message,
            "data": data
        }), status_code

    @staticmethod
    def error(message="Error", errors=None, status_code=400):
        return jsonify({
            "success": False,
            "message": message,
            "errors": errors
        }), status_code


def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return ApiResponse.error("Invalid or missing token", status_code=401)

        token = auth_header.split(" ")[1]

        try:
            payload = decode_token(token)
            user = User.query.get(payload["user_id"])
            if not user:
                return ApiResponse.error("User not found", status_code=401)
        except jwt.ExpiredSignatureError:
            return ApiResponse.error("Token expired", status_code=401)
        except Exception:
            return ApiResponse.error("Invalid token", status_code=401)

        return f(current_user=user, *args, **kwargs)
    return wrapper