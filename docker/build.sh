docker-compose build
docker-compose run python3-x64
mv ../bin/apim.exe ../bin/apim-python3-Qt5-x64.exe
docker-compose run python3-x86
mv ../bin/apim.exe ../bin/apim-python3-Qt5-x86-32bit.exe
