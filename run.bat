@echo off
cd /d "%~dp0"
python process_pdfs.py --folder "%cd%" --recursive --output both
pause
