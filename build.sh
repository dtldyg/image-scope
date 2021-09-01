pyinstaller -F -w -i res/ico.ico --add-data 'res/*;res' -n 图像-色彩分析器 src/main.py

rm 图像-色彩分析器.spec
rm -r build
