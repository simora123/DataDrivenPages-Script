rem : /k is for interactive run, /c is for scheduled run and requires full UNC path
set mytime=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%
set mytime=%mytime: =%


cmd /c \\YCPCFS\GIS_Projects\IS\Scripts\Python\Printing\TaxParcel_DataDrivenPages_Update.py > ^
\\YCPCFS\GIS_Projects\IS\Scripts\Python\Logs\TaxParcel_DataDrivenPages_Update_%mytime%.txt 2>&1