import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.db import connection

class User:
    """简单的用户类，用于Django REST Framework认证"""
    def __init__(self, user_id, username, role, status):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.status = status
        self.is_authenticated = True
        self.is_anonymous = False

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        if not token:
            return None
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Invalid token')
            
            # 使用原生SQL查询用户信息
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, username, role, status 
                    FROM users 
                    WHERE user_id = %s
                """, [user_id])
                user_data = cursor.fetchone()
                
                if not user_data:
                    raise AuthenticationFailed('User not found')
                
                if user_data[3] != 1:  # status != 1
                    raise AuthenticationFailed('User account disabled')
                
                # 创建用户对象
                user = User(user_data[0], user_data[1], user_data[2], user_data[3])
                return (user, token)
                
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
