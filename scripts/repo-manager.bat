@echo off
REM CodeTraceAI 仓库管理脚本
REM Windows 批处理文件

echo ==================================================
echo CodeTraceAI 仓库管理
echo ==================================================
echo.
echo 远程仓库: https://codeup.aliyun.com/639060c273a727212a3e3fe2/python/CodeTraceAI.git
echo.

:menu
echo 请选择操作:
echo   1. 查看仓库状态
echo   2. 查看最近提交
echo   3. 查看修改内容
echo   4. 同步代码 (fetch + push)
echo   5. 打开远程仓库
echo   6. 查看所有分支
echo   0. 退出
echo.

set /p choice=请输入选择 (0-6):

if "%choice%"=="1" goto status
if "%choice%"=="2" goto log
if "%choice%"=="3" goto diff
if "%choice%"=="4" goto sync
if "%choice%"=="5" goto open
if "%choice%"=="6" goto branch
if "%choice%"=="0" goto end
goto menu

:status
echo.
echo ==================================================
echo 仓库状态
echo ==================================================
git status -sb
echo.
pause
goto menu

:log
echo.
echo ==================================================
echo 最近提交记录
echo ==================================================
git log --oneline --graph -10
echo.
pause
goto menu

:diff
echo.
echo ==================================================
echo 修改统计
echo ==================================================
git diff --stat
echo.
pause
goto menu

:sync
echo.
echo ==================================================
echo 同步代码
echo ==================================================
echo 获取远程更新...
git fetch origin
echo.
echo 推送本地更改...
git push origin master
echo.
pause
goto menu

:open
echo.
start https://codeup.aliyun.com/639060c273a727212a3e3fe2/python/CodeTraceAI
goto menu

:branch
echo.
echo ==================================================
echo 所有分支
echo ==================================================
git branch -a
echo.
pause
goto menu

:end
echo 退出
