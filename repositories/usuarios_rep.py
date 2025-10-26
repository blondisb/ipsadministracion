from typing import Optional, Dict, Any
from supabase import Client
from repositories.supabase_client import obtener_cliente_supabase
from schemas.auth_sch import UsuarioCrear
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RepositorioUsuarios:
    def __init__(self, cliente: Client = None):
        self.cliente = cliente or obtener_cliente_supabase()
        self.tabla = "usuarios"
    
    def obtener_usuario_por_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            respuesta = self.cliente.table(self.tabla).select("*").eq("email", email).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error obteniendo usuario por email {email}: {e}")
            return None
    
    def obtener_usuario_por_id(self, id_usuario: int) -> Optional[Dict[str, Any]]:
        try:
            respuesta = self.cliente.table(self.tabla).select("*").eq("id", id_usuario).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error obteniendo usuario {id_usuario}: {e}")
            return None
    
    def crear_usuario(self, usuario: UsuarioCrear) -> Optional[Dict[str, Any]]:
        try:
            # Hashear la contraseña antes de guardar
            datos_usuario = usuario.dict()
            datos_usuario['contraseña_hash'] = pwd_context.hash(usuario.contraseña)
            del datos_usuario['contraseña']  # Eliminar contraseña en texto plano
            
            respuesta = self.cliente.table(self.tabla).insert(datos_usuario).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return None
    
    def verificar_contraseña(self, contraseña_plano: str, contraseña_hash: str) -> bool:
        return pwd_context.verify(contraseña_plano, contraseña_hash)