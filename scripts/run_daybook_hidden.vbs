' Inicia StellarDaybook sin ventana de consola.
' Edita PYTHONW y REPO según tu máquina.

Option Explicit
Dim sh, PYTHONW, REPO, cmd
Set sh = CreateObject("WScript.Shell")

' Ruta a pythonw.exe del venv (o instalación global).
PYTHONW = "C:\Users\Jack\Documents\GitHub\Experimentos\StellarDaybook\.venv\Scripts\pythonw.exe"

' Raíz del repositorio (por si el perfil de Python lo necesita explícito).
REPO = "C:\Users\Jack\Documents\GitHub\Experimentos\StellarDaybook"

cmd = """" & PYTHONW & """ -m stellar_daybook"
sh.CurrentDirectory = REPO
sh.Run cmd, 0, False
