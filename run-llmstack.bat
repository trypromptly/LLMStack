@echo off
setlocal

rem set LLMSTACK_PORT and other environment variables
if exist .env (
  for /F "delims=# eol=# tokens=1,2" %%i in (.env) do set "%%i=%%j"
) else (
  echo ".env file not found"
  exit /B
)

start /B docker-compose up -d --pull always

:loop
  rem make a curl request and store the output
  for /F "delims=" %%i in ('curl -s -o NUL -w "%%{http_code}" http://localhost:%LLMSTACK_PORT%') do set "response=%%i"
  
  rem if the output is not 200, sleep for 3 seconds then try again
  if not "%response%"=="200" (
    echo Waiting for LLMStack to be ready...
    rem choice is used as a sleep function in Windows batch files
    choice /T 3 /D Y /N > NUL
    goto loop
  )
  
echo LLMStack is ready!

rem open the web browser
start http://localhost:%LLMSTACK_PORT%

:end
endlocal