from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

seguridad = HTTPBearer()

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def obtener_usuario_actual(credenciales: HTTPAuthorizationCredentials = Depends(seguridad)):
    token = credenciales.credentials
    payload = verificar_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def crear_token_acceso(datos: dict):
    from services.auth_srv import ServicioAutenticacion
    from repositories.usuarios_rep import RepositorioUsuarios
    
    repositorio = RepositorioUsuarios()
    servicio = ServicioAutenticacion(repositorio)
    return servicio.crear_token_acceso(datos)