# 🏥 API Médica - Sistema de Gestión de Pacientes y Citas

![Arquitectura del proyecto](doc_media/appdiagram.png)

## 📋 Descripción

API REST desarrollada con **FastAPI** para la gestión integral de pacientes y citas médicas. Incluye un asistente virtual con IA para agendar citas de manera inteligente.

## ✨ Características Principales

### 🎯 Funcionalidades Core
- **Gestión de Pacientes**: CRUD completo de pacientes
- **Gestión de Citas**: Agendamiento y consulta de citas médicas
- **Validación de Disponibilidad**: Verificación en tiempo real de horarios disponibles
- **Autenticación JWT**: Sistema seguro de autenticación
- **Asistente IA**: Agendamiento inteligente con lenguaje natural

### 🤖 Asistente Virtual Inteligente
- **Procesamiento de Lenguaje Natural**: Entiende frases como "quiero cita con el doctor Pérez mañana a las 10"
- **Búsqueda Automática**: Encuentra médicos por nombre o especialidad
- **Verificación de Disponibilidad**: Consulta horarios disponibles en tiempo real
- **Creación Automática de Citas**: Agenda citas automáticamente cuando se proporciona ID de paciente

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno y rápido
- **Python 3.11** - Lenguaje de programación
- **Supabase** - Base de datos PostgreSQL en la nube
- **JWT** - Autenticación con tokens
- **bcrypt** - Hash de contraseñas seguro

### IA y Agentes
- **crewAI** - Framework para agentes de IA
- **Groq** - Plataforma de inferencia de IA de alta velocidad
- **Llama 3** - Modelo de lenguaje para el asistente

### DevOps
- **Docker** - Contenerización de la aplicación
- **Google Cloud Run** - Plataforma de despliegue
- **GitHub Actions** - CI/CD automático

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.11 o superior
- Cuenta en [Supabase](https://supabase.com)
- Cuenta en [Groq](https://groq.com) (para el asistente IA)
- Cuenta en [Google Cloud](https://cloud.google.com) (para despliegue)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/blondisb/ipsadministracion.git
cd api-medica
```

### 2. Configurar Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 3. Instalar Dependencias
```bash
pip install -r requisitos.txt
```

### 4. Configurar Variables de Entorno
Crear archivo `.env`:

```env
# Supabase
URL_SUPABASE=https://tu-proyecto.supabase.co
CLAVE_API_SUPABASE=tu-clave-supabase

# JWT
CLAVE_SECRETA=tu-clave-secreta-muy-segura
ALGORITMO=HS256
MINUTOS_EXPIRACION_TOKEN=30

# Groq (Para el asistente IA)
GROQ_API_KEY=tu-api-key-de-groq

# CORS
ORIGENES_PERMITIDOS=http://localhost:3000,http://127.0.0.1:3000
```

### 5. Configurar Base de Datos
Ejecutar el script SQL en la consola de Supabase para crear las tablas necesarias.

### 6. Crear Usuario Administrador
```bash
python crear_usuario_admin.py
```

### 7. Ejecutar la Aplicación
```bash
uvicorn principal:app --reload
```

La API estará disponible en: https://ipsadministracion-938932231856.us-east1.run.app/ ó http://localhost:8000
Ya está desplegada en google cloud.

## 📚 Documentación de la API

### Autenticación
La API usa autenticación JWT. Incluye el token en el header:

```
Authorization: Bearer <tu_token>
```

### Endpoints Principales

#### 🔐 Autenticación
- `POST /auth/login` - Iniciar sesión
- `POST /auth/registro` - Registrar nuevo usuario

#### 👥 Pacientes
- `GET /patients` - Listar pacientes
- `POST /patients` - Crear paciente
- `GET /patients/{id}` - Obtener paciente específico
- `PUT /patients/{id}` - Actualizar paciente
- `DELETE /patients/{id}` - Eliminar paciente

#### 📅 Citas
- `GET /appointments` - Listar todas las citas
- `POST /appointments` - Crear cita
- `GET /appointments/{id}` - Obtener cita específica
- `PUT /appointments/{id}` - Actualizar cita
- `POST /appointments/verificar-disponibilidad` - Verificar disponibilidad

#### 🕒 Disponibilidad
- `GET /availability/profesional/{id}` - Horarios disponibles de un médico
- `GET /availability/profesionales/activos` - Listar profesionales activos

#### 🤖 Asistente IA
- `POST /assistant` - Procesar solicitud de agendamiento con IA

### Documentación Interactiva
- **Swagger UI**: https://ipsadministracion-938932231856.us-east1.run.app/docs o http://localhost:8000/docs
- **ReDoc**: https://ipsadministracion-938932231856.us-east1.run.app/redoc o http://localhost:8000/redoc

## 🧠 Uso del Asistente IA

### Ejemplo de Solicitud
```bash
POST /assistant
Content-Type: application/json

{
  "mensaje": "quiero agendar cita con el doctor Pérez mañana a las 10 de la mañana",
  "paciente_id": 1
}
```

### Respuesta del Asistente
```json
{
  "nombre_doctor": "Dr. Carlos Pérez",
  "fecha": "2024-01-16",
  "hora": "10:00",
  "profesional_id": 2,
  "disponible": true,
  "cita_creada": true,
  "cita_id": 15,
  "mensaje": "✅ Cita creada exitosamente con el Dr. Carlos Pérez para el 2024-01-16 a las 10:00"
}
```

## 🐳 Despliegue con Docker

### Construir la Imagen
```bash
docker build -t api-medica .
```

### Ejecutar Contenedor
```bash
docker run -p 8000:8000 --env-file .env api-medica
```

### Despliegue en Google Cloud Run
El proyecto incluye configuración para despliegue automático en Google Cloud Run mediante GitHub Actions.

## 🗄️ Estructura del Proyecto

```
api-medica/
├── enrutadores/          # Endpoints de la API
├── servicios/           # Lógica de negocio
├── repositorios/        # Acceso a datos
├── esquemas/           # Modelos Pydantic
├── herramientas/        # Tools para crewAI
├── utilidades/         # Funciones auxiliares
├── principal.py        # Aplicación FastAPI
├── configuracion.py    # Configuración
├── requisitos.txt      # Dependencias
├── Dockerfile          # Configuración Docker
├── cloudbuild.yaml     # Google Cloud Build
└── README.md          # Este archivo
```

## 🔧 Desarrollo

### Ejecutar Tests
```bash
pytest tests/
```

### Formatear Código
```bash
black .
```

### Verificar Tipos
```bash
mypy .
```



## 👥 Autores

**Tu Nombre** - [tu-usuario](https://github.com/blondisb)

## 🙏 Agradecimientos

- **FastAPI** - Por el excelente framework
- **Supabase** - Por la base de datos en la nube
- **crewAI** - Por el framework de agentes
- **Groq** - Por la plataforma de provision de hardware para LLMs