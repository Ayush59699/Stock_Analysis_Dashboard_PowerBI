# Activate .env and install requirements, and run the server
& ".\.env\Scripts\Activate.ps1"
& ".\.env\Scripts\pip.exe" install -r req.txt
& ".\.env\Scripts\python.exe" app.py
