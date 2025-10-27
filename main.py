from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.security import obtener_usuario_actual
from config import settings
from routers import pacientes, citas, disponibilidad, iaasistente, auth

app = FastAPI(
    title="Medical Appointment API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


@app.get("/")
async def root():
    return {"message": "Medical Appointment API"}


app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Autenticación"]
)

app.include_router(
    pacientes.router,
    prefix="/patients",
    tags=["Pacientes"]
    # ,dependencies=[Depends(obtener_usuario_actual)]
)

app.include_router(
    citas.router,
    prefix="/citas",
    tags=["Citas"]
    # ,dependencies=[Depends(obtener_usuario_actual)]
)

# Nuevo enrutador de disponibilidad
app.include_router(
    disponibilidad.router,
    prefix="/availability",
    tags=["Disponibilidad"]
    # ,dependencies=[Depends(obtener_usuario_actual)]
)

app.include_router(
    iaasistente.router,
    prefix="/assistant",
    tags=["Asistente IA"]
    # ,dependencies=[Depends(obtener_usuario_actual)]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)