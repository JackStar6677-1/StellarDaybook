' Inicia StellarDaybook sin consola. Rutas relativas al repo (carpeta padre de \scripts).
Option Explicit
Dim sh, fso, repo, pyw
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

repo = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
pyw = fso.BuildPath(repo, ".venv\Scripts\pythonw.exe")

If Not fso.FileExists(pyw) Then
  ' Sin MsgBox para no molestar en inicio; codigo 1 = falta venv o install no ejecutado
  WScript.Quit 1
End If

sh.CurrentDirectory = repo
sh.Run """" & pyw & """ -m stellar_daybook", 0, False
