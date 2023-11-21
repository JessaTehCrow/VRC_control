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
--onefile ^
--standalone ^
--show-memory ^
--follow-imports ^
--disable-console ^
--enable-plugin=tk-inter ^
--include-data-dir=sounds=sounds/ ^
--output-filename="VRC Control" ^
--product-name="VRC Control" ^
--company-name="Crowde" ^
--product-version="2.0" ^
--file-description="Control VRC Parameters through the web" ^
--include-data-file="data/CTRL.ico"="data/" ^
--windows-icon-from-ico="data/CTRL.ico" ^
--output-dir="../../dist" ^
main.py

echo.
echo.
echo.
echo.
echo.
pause