@echo off
echo [Arena AutoCache Bootstrap v2.0] Test Script
echo.

echo Testing Debug mode...
call arena_bootstrap_cache_v2.bat --debug
echo.

echo Testing Production mode...
call arena_bootstrap_cache_v2.bat --prod
echo.

echo Testing Restore defaults...
call arena_bootstrap_cache_v2.bat --restore-defaults
echo.

echo Testing Help...
call arena_bootstrap_cache_v2.bat --help
echo.

echo All tests completed!
pause
