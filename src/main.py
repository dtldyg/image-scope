# coding=utf-8

import sys
import math
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


def hl_2_xy(w, h, h_f, l_f):
	return round(w * h_f), round(h * l_f)


def hs_2_xy(r, h_f, s_f):
	radian = 2 * math.pi * h_f
	mod = r * s_f
	return -round(mod * math.sin(radian)), -round(mod * math.cos(radian))


def draw_line(scope):
	for x1 in range(0, scope.width(), 3):
		scope.setPixelColor(x1, int(scope.height() / 2), QColor(50, 50, 50))
	for y1 in range(0, scope.height(), 3):
		scope.setPixelColor(int(scope.width() / 2), y1, QColor(50, 50, 50))


def draw_h_bar(w, h, b, scope):
	for x1 in range(0, w):
		for y1 in range(0, b):
			c1 = QColor()
			c1.setHslF(x1 / w, 0.8, (b - y1) / b / 2)
			scope.setPixelColor(x1, y1 + h, c1)


if __name__ == '__main__':
	app = QApplication(sys.argv)

	radius = 150
	width = 300
	height = 280
	bar = 20

	image = QImage('res/image2.jpg')
	scope1 = QImage('res/scope.jpg')
	draw_line(scope1)
	draw_h_bar(width, height, bar, scope1)
	scope2 = QImage('res/scope.jpg')
	draw_line(scope2)
	hl_points = {}
	hs_points = {}
	jump = max(1, round(math.sqrt(image.width() * image.height() / 5000)))

	# 分析像素
	for x in range(0, image.width(), jump):
		for y in range(0, image.height(), jump):
			color: QColor = image.pixelColor(x, y)
			x_hl, y_hl = hl_2_xy(width, height, color.hslHueF(), color.lightnessF())
			x_hs, y_hs = hs_2_xy(radius, color.hslHueF(), color.hslSaturationF())
			if (x_hl, y_hl) not in hl_points:
				c = QColor()
				c.setHslF(color.hslHueF(), color.hslSaturationF(), color.lightnessF())
				hl_points[(x_hl, y_hl)] = c
			if (x_hs, y_hs) not in hs_points:
				c = QColor()
				c.setHslF(color.hslHueF(), color.hslSaturationF(), color.lightnessF())
				hs_points[(x_hs, y_hs)] = c

	# 波形示波器（x-色相，y-亮度）
	for pos, color in hl_points.items():
		color.setHslF(color.hslHueF(), 0.5, color.lightnessF() * 0.9 + 0.1)
		scope1.setPixelColor(pos[0], height - pos[1], color)

	# 矢量示波器
	for pos, color in hs_points.items():
		color.setHslF(color.hslHueF(), color.hslSaturationF(), 0.5)
		scope2.setPixelColor(pos[0] + radius, pos[1] + radius, color)

	label_image = QLabel()
	label_image.setFixedSize(610, 300)
	label_image.setScaledContents(True)
	label_image.setPixmap(QPixmap(image))

	label_scope1 = QLabel()
	label_scope1.setFixedSize(300, 300)
	label_scope1.setScaledContents(True)
	label_scope1.setPixmap(QPixmap(scope1))

	label_scope2 = QLabel()
	label_scope2.setFixedSize(300, 300)
	label_scope2.setScaledContents(True)
	label_scope2.setPixmap(QPixmap(scope2))

	layout = QVBoxLayout()
	layout_scope = QHBoxLayout()
	layout.addWidget(label_image)
	layout.addLayout(layout_scope)
	layout_scope.addWidget(label_scope1)
	layout_scope.addWidget(label_scope2)

	window = QWidget()
	window.setLayout(layout)
	window.setFixedSize(634, 640)
	window.setWindowTitle("Image Scope")
	window.show()

	sys.exit(app.exec_())
