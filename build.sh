pyinstaller -F -w -i res/icon.ico --add-data 'res/*;res' -n 图像示波器 src/main.py

rm 图像示波器.spec
rm -r build
