# coding=utf-8

import sys
from PyQt5.QtWidgets import *

if __name__ == '__main__':
	app = QApplication(sys.argv)

	window = QWidget()
	window.setFixedSize(300, 300)
	window.setWindowTitle("drop")

	window.show()
	sys.exit(app.exec_())
