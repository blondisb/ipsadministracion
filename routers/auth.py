from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from repositories.usuarios_rep import RepositorioUsuarios
from services.auth_srv import ServicioAutenticacion
from schemas.auth_sch import Token, UsuarioLogin, UsuarioCrear, Usuario
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def obtener_servicio_autenticacion() -> ServicioAutenticacion:
    repositorio_usuarios = RepositorioUsuarios()
    return ServicioAutenticacion(repositorio_usuarios)

@router.post("/login", response_model=Token)
def login(
    datos_login: UsuarioLogin,
    servicio: ServicioAutenticacion = Depends(obtener_servicio_autenticacion)
):
    """
    Iniciar sesión y obtener token de acceso
    """
    return servicio.login(datos_login)

@router.post("/login-formulario", response_model=Token)
def login_formulario(
    form_data: OAuth2PasswordRequestForm = Depends(),
    servicio: ServicioAutenticacion = Depends(obtener_servicio_autenticacion)
):
    """
    Iniciar sesión usando OAuth2 form data (compatible con Postman)
    """
    datos_login = UsuarioLogin(email=form_data.username, contraseña=form_data.password)
    return servicio.login(datos_login)

@router.post("/registro", response_model=Usuario)
def registrar_usuario(
    usuario: UsuarioCrear,
    servicio_autenticacion: ServicioAutenticacion = Depends(obtener_servicio_autenticacion)
):
    """
    Registrar nuevo usuario
    """
    repositorio = RepositorioUsuarios()
    
    # Verificar si el usuario ya existe
    usuario_existente = repositorio.obtener_usuario_por_email(usuario.email)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear usuario
    usuario_creado = repositorio.crear_usuario(usuario)
    if not usuario_creado:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario"
        )
    
    # Eliminar información sensible antes de retornar
    usuario_creado.pop('contraseña_hash', None)
    
    return Usuario(**usuario_creado)

@router.get("/verificar-token")
def verificar_token(
    usuario_actual: dict = Depends(obtener_servicio_autenticacion)
):
    """
    Verificar si el token es válido
    """
    return {
        "mensaje": "Token válido",
        "usuario": {
            "id": usuario_actual.get("sub"),
            "email": usuario_actual.get("email"),
            "nombre": usuario_actual.get("nombre")
        }
    }