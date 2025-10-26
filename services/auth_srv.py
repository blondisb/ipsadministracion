from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import settings

class ServicioAutenticacion:
    @staticmethod
    def crear_token_acceso(datos: dict, duracion_expiracion: timedelta = None):
        datos_codificar = datos.copy()
        if duracion_expiracion:
            expiracion = datetime.utcnow() + duracion_expiracion
        else:
            expiracion = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        datos_codificar.update({"exp": expiracion})
        token_codificado = jwt.encode(datos_codificar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return token_codificado