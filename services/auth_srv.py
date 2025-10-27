from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
from config import settings
from repositories.usuarios_rep import RepositorioUsuarios
from schemas.auth_sch import UsuarioLogin, Token
import logging

logger = logging.getLogger(__name__)

class ServicioAutenticacion:
    def __init__(self, repositorio_usuarios: RepositorioUsuarios):
        self.repositorio_usuarios = repositorio_usuarios
    
    def autenticar_usuario(self, email: str, contraseña: str):
        usuario = self.repositorio_usuarios.obtener_usuario_por_email(email)
        if not usuario:
            return False
        if not self.repositorio_usuarios.verificar_contraseña(contraseña, usuario['contraseña_hash']):
            return False
        return usuario
    
    def crear_token_acceso(self, datos: dict, duracion_expiracion: timedelta = None):
        datos_codificar = datos.copy()
        if duracion_expiracion:
            expire = datetime.utcnow() + duracion_expiracion
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        datos_codificar.update({"exp": expire})
        encoded_jwt = jwt.encode(datos_codificar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def login(self, datos_login: UsuarioLogin) -> Token:
        usuario = self.autenticar_usuario(datos_login.email, datos_login.contraseña)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        datos_token = {
            "sub": str(usuario['id']),
            "email": usuario['email'],
            "nombre": usuario['nombre']
        }
        
        token_acceso = self.crear_token_acceso(datos_token)
        return Token(token_acceso=token_acceso, tipo_token="bearer")