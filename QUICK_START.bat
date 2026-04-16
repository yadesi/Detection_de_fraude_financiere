@echo off
echo ==========================================
echo FRAUD DETECTION SYSTEM - QUICK START
echo ==========================================
echo.

echo [1/5] Verification de Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Docker n'est pas installe!
    echo Veuillez installer Docker Desktop depuis: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo Docker est installe!

echo.
echo [2/5] Arret des services existants...
docker-compose down -v

echo.
echo [3/5] Demarrage de tous les services...
docker-compose up -d

echo.
echo [4/5] Attente du demarrage complet (30 secondes)...
timeout /t 30 /nobreak

echo.
echo [5/5] Verification des services...
docker-compose ps

echo.
echo ==========================================
echo SYSTEME PRET!
echo ==========================================
echo.
echo Services accessibles:
echo - Frontend React:     http://localhost:3000
echo - API Documentation:  http://localhost:8000/docs
echo - Dashboard Streamlit: http://localhost:8501
echo - Grafana:           http://localhost:3000 (admin/admin)
echo - Prometheus:        http://localhost:9090
echo - MLflow:            http://localhost:5000
echo.
echo Test de l'API:
curl http://localhost:8000/health
echo.
echo Pour arreter le systeme: docker-compose down
echo.
pause
