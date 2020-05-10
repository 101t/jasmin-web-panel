@ECHO OFF
set ENVIROO=python

set MANAGER=manage.py

CALL env\Scripts\activate

set init_result=F
if "%~1"=="--init" set init_result=T
if "%~1"=="-i" set init_result=T
if "%init_result%"=="T" (
    echo - Deleting sqlite database if exist ...
    del /F db.sqlite3
    echo - Reset all migrations files ...
    %ENVIROO% %MANAGER% reseter
    echo - Make new migrations files ...
    %ENVIROO% %MANAGER% makemigrations core
    %ENVIROO% %MANAGER% makemigrations users
    %ENVIROO% %MANAGER% makemigrations notify
    %ENVIROO% %MANAGER% makemigrations
    echo - Migrate database ...
    %ENVIROO% %MANAGER% migrate
    echo - Loading new data samples ...
    %ENVIROO% %MANAGER% load_new
)

set RUN_PROJECT=%ENVIROO% %MANAGER% runserver 0.0.0.0:8000
echo %RUN_PROJECT%
CALL %RUN_PROJECT%