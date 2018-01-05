set release_dir=release5
E:\Python27\python.exe E:\Python27\Scripts\cxfreeze getDoc5.py -OO -c --target-dir %release_dir% --include-modules=idna.idnadata --target-name=free_doc.exe --icon=free_doc.ico
md %release_dir%\phantomjs
copy phantomjs\phantomjs.exe %release_dir%\phantomjs
copy parameters.ini %release_dir%