rem pyinstaller -F --noconsole main.py --splash docs/background.png -i docs/IFX_Logo.ico --name main_auto_logger.exe
pyinstaller -F --noconsole main.py -i docs/IFX_Logo.ico --name iftw_logger.exe
pyinstaller -F main.py -i docs/IFX_Logo.ico --name iftw_logger_console.exe
copy dist\iftw_logger.exe binary\.
copy dist\iftw_logger_console.exe binary\.
del *.spec
rmdir build /s /q
rmdir dist /s /q
PAUSE