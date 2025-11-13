@echo off
echo === Migration des modeles de jeu ===
cd backend
python manage.py makemigrations games
python manage.py migrate games
echo.
echo === Migration terminee ===
pause
