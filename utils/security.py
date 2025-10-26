from jose import JWTError, jwt
from fastapi import HTTPException, status
from config import settings

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def crear_token_acceso(datos: dict):
    from servicios.servicio_autenticacion import ServicioAutenticacion
    return ServicioAutenticacion.crear_token_acceso(datos)