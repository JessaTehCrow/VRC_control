@Echo off
pushd ..
set parent=%cd%
popd

echo.
echo .------------------------------------.
echo : Compiling main.py into onefile exe :
echo '------------------------------------'
echo Output File: %parent%\dist\main.exe
echo.
echo.

py -m nuitka ^
--follow-imports ^
--output-dir="../dist" ^
--enable-plugin=tk-inter ^
--standalone ^
--include-data-dir=sounds=sounds/ ^
--onefile ^
--windows-icon-from-ico="data/CTRL.ico" ^
--include-data-file="data/CTRL.ico"="data/" ^
--disable-console ^
main.py

echo.
echo.
echo.
echo.
echo.
pause