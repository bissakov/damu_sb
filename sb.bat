@echo off
set "ROOT=%~dp0"
pushd %ROOT%src

%ROOT%venv\Scripts\python.exe -m sb.main
popd
