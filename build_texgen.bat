@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64 -vcvars_ver=14.44.35207
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set CUDA_PATH=%CUDA_HOME%
set PATH=%CUDA_HOME%\bin;%PATH%
set DISTUTILS_USE_SDK=1
set PY="C:\Users\self_\OneDrive\Documents\Modly\extensions\hunyuan3d-mini-turbo\venv\Scripts\python.exe"

echo === Building custom_rasterizer (wheel) ===
cd /d "C:\Users\self_\OneDrive\Documents\Modly\models\hunyuan3d-mini-turbo\generate\_hy3dgen\hy3dgen\texgen\custom_rasterizer"
%PY% -m pip install --no-build-isolation --force-reinstall --no-deps .
if errorlevel 1 (echo RASTERIZER_BUILD_FAILED & exit /b 1)

echo === Building differentiable_renderer (wheel) ===
cd /d "C:\Users\self_\OneDrive\Documents\Modly\models\hunyuan3d-mini-turbo\generate\_hy3dgen\hy3dgen\texgen\differentiable_renderer"
%PY% -m pip install --no-build-isolation --force-reinstall --no-deps .
if errorlevel 1 (echo RENDERER_BUILD_FAILED & exit /b 1)

echo === BOTH EXTENSIONS BUILT ===
