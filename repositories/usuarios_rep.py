from typing import List, Optional, Dict, Any
from supabase import Client
from repositories.supabase_client import obtener_cliente_supabase
from schemas.auth_sch import UsuarioCrear
import logging
import bcrypt

logger = logging.getLogger(__name__)

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
            # Verificar y limpiar la contraseña
            contraseña = usuario.contraseña.strip()
            
            # Validar longitud máxima para bcrypt
            if len(contraseña) > 72:
                logger.warning("Contraseña demasiado larga, truncando a 72 caracteres")
                contraseña = contraseña[:72]
            
            # Validar que la contraseña no esté vacía
            if not contraseña:
                logger.error("La contraseña no puede estar vacía")
                return None
            
            # Hashear la contraseña usando bcrypt directamente
            contraseña_bytes = contraseña.encode('utf-8')
            salt = bcrypt.gensalt()
            contraseña_hash = bcrypt.hashpw(contraseña_bytes, salt).decode('utf-8')
            
            # Preparar datos del usuario
            datos_usuario = {
                "email": usuario.email,
                "contraseña_hash": contraseña_hash,
                "nombre": usuario.nombre,
                "apellido": usuario.apellido,
                "activo": True
            }
            
            respuesta = self.cliente.table(self.tabla).insert(datos_usuario).execute()
            return respuesta.data[0] if respuesta.data else None
            
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return None
    
    def verificar_contraseña(self, contraseña_plano: str, contraseña_hash: str) -> bool:
        try:
            contraseña_bytes = contraseña_plano.encode('utf-8')
            hash_bytes = contraseña_hash.encode('utf-8')
            return bcrypt.checkpw(contraseña_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            return False
    
    def obtener_usuarios(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            respuesta = self.cliente.table(self.tabla).select("*").range(skip, skip + limit - 1).execute()
            return respuesta.data
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
            return []