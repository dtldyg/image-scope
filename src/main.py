# coding=utf-8

import sys
import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

WINDOW_TITLE = 'Image Scope'
WINDOW_SIZE = (634, 640)
IMAGE_SIZE = (610, 300)
SCOPE_SIZE = (300, 300)
SCOPE_RADIUS = int(SCOPE_SIZE[0] / 2)
SCOPE_BAR = 20
ANALYSE_POINTS = 5000
SCALE_MAX = 6
SCALE_STEP = 0.12


class ImageLabel(QLabel):
	def __init__(self, parent):
		super(ImageLabel, self).__init__()
		self.parent = parent
		self.press_anchor = None

	@property
	def label_image(self):
		return self.parent.label_image

	@property
	def image_image(self):
		return self.parent.image_image

	@property
	def image_scale(self):
		return self.parent.image_scale

	@image_scale.setter
	def image_scale(self, value):
		self.parent.image_scale = value

	# ↓↓ wheel event
	def wheelEvent(self, event):
		if self.image_scale == 0 or event.angleDelta().y() == 0:
			return
		if event.angleDelta().y() > 0:
			self.image_scale = min_f(SCALE_MAX, self.image_scale + SCALE_STEP)
		else:
			self.image_scale = max_f(1, self.image_scale - SCALE_STEP)
		new_size = (int(IMAGE_SIZE[0] * self.image_scale), int(IMAGE_SIZE[1] * self.image_scale))
		self.label_image.setPixmap(QPixmap(self.image_image).scaled(*new_size, Qt.KeepAspectRatio))

	# ↓↓ mouse click event
	def mouseReleaseEvent(self, event):
		if self.image_scale == 0:
			return
		if event.button() == Qt.LeftButton:
			self.press_anchor = None
		elif event.button() == Qt.RightButton:
			self.image_scale = 1
			new_size = (int(IMAGE_SIZE[0] * self.image_scale), int(IMAGE_SIZE[1] * self.image_scale))
			self.label_image.setPixmap(QPixmap(self.image_image).scaled(*new_size, Qt.KeepAspectRatio))

	# ↓↓ mouse press event
	def mousePressEvent(self, event):
		if self.image_scale == 0 or event.button() != Qt.LeftButton:
			return
		self.press_anchor = event.pos()

	# ↓↓ mouse move event
	def mouseMoveEvent(self, event):
		pass


class WindowWidget(QWidget):
	def __init__(self):
		super(WindowWidget, self).__init__()
		self.label_image = None
		self.image_image = None
		self.image_scale = 0
		self.label_scope1 = None  # 波形示波器
		self.image_scope1 = None
		self.label_scope2 = None  # 矢量示波器
		self.image_scope2 = None
		self.setAcceptDrops(True)
		self.init_ui()
		self.reg_shortcut()

	# ↓↓ init layout & widget
	def init_ui(self):
		self.init_scopes()

		self.image_image = QImage('res/empty.jpg')
		self.label_image = ImageLabel(self)
		self.label_image.setFixedSize(*IMAGE_SIZE)
		self.label_image.setAlignment(Qt.AlignCenter)
		self.label_image.setStyleSheet('border: 1px solid #cccccc')
		self.label_image.setPixmap(QPixmap(self.image_image))

		self.label_scope1 = QLabel()
		self.label_scope1.setFixedSize(*SCOPE_SIZE)
		self.label_scope1.setPixmap(QPixmap(self.image_scope1))

		self.label_scope2 = QLabel()
		self.label_scope2.setFixedSize(*SCOPE_SIZE)
		self.label_scope2.setPixmap(QPixmap(self.image_scope2))

		layout = QVBoxLayout()
		layout.addWidget(self.label_image)
		layout_scopes = QHBoxLayout()
		layout_scopes.addWidget(self.label_scope1)
		layout_scopes.addWidget(self.label_scope2)
		layout.addLayout(layout_scopes)

		self.setLayout(layout)
		self.setFixedSize(*WINDOW_SIZE)
		self.setWindowTitle(WINDOW_TITLE)

	def init_scopes(self):
		self.image_scope1 = QImage('res/scope1.jpg')
		self.image_scope2 = QImage('res/scope2.jpg')

	# ↓↓ reg shortcut
	def reg_shortcut(self):
		shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
		shortcut_open.activated.connect(self.on_open)
		shortcut_paste = QShortcut(QKeySequence("Ctrl+V"), self)
		shortcut_paste.activated.connect(self.paste_image)

	# ↓↓ drop event
	def dragEnterEvent(self, event):
		text = event.mimeData().text()
		if text.endswith('.jpg') or text.endswith('.png') or text.endswith('.jpeg') or text.endswith('.bmp'):
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		path = event.mimeData().text().replace('file:///', '')
		self.load_image(path)

	# ↓↓ open event
	@pyqtSlot()
	def on_open(self):
		file = QFileDialog.getOpenFileName(self, '打开文件', '.', '*.jpg;*.png;*.jpeg;*.bmp')
		if file[0]:
			self.load_image(file[0])

	# ↓↓ paste event
	@pyqtSlot()
	def paste_image(self):
		image = QApplication.clipboard().pixmap().toImage()
		if not image.isNull():
			self.image_image = image
			self.refresh_image()

	# ↓↓ new image
	def load_image(self, path):
		self.image_image = QImage(path)
		self.refresh_image()

	def refresh_image(self):
		self.init_scopes()

		hl_points = {}
		hl_w = SCOPE_SIZE[0]
		hl_h = SCOPE_SIZE[1] - SCOPE_BAR
		hs_points = {}

		# 分析像素
		jump = max(1, round(math.sqrt(self.image_image.width() * self.image_image.height() / ANALYSE_POINTS)))
		for x in range(0, self.image_image.width(), jump):
			for y in range(0, self.image_image.height(), jump):
				color: QColor = self.image_image.pixelColor(x, y)
				x_hl, y_hl = hl_2_xy(hl_w, hl_h, color.hslHueF(), color.lightnessF())
				x_hs, y_hs = hs_2_xy(SCOPE_RADIUS, color.hslHueF(), color.hslSaturationF())
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
			self.image_scope1.setPixelColor(pos[0], hl_h - pos[1], color)

		# 矢量示波器
		for pos, color in hs_points.items():
			color.setHslF(color.hslHueF(), color.hslSaturationF(), 0.5)
			self.image_scope2.setPixelColor(pos[0] + SCOPE_RADIUS, pos[1] + SCOPE_RADIUS, color)

		self.image_scale = 1
		self.label_image.setPixmap(QPixmap(self.image_image).scaled(*IMAGE_SIZE, Qt.KeepAspectRatio))
		self.label_scope1.setPixmap(QPixmap(self.image_scope1))
		self.label_scope2.setPixmap(QPixmap(self.image_scope2))


def hl_2_xy(w, h, h_f, l_f):
	return round(w * h_f), round(h * l_f)


def hs_2_xy(r, h_f, s_f):
	radian = 2 * math.pi * h_f
	mod = r * s_f
	return -round(mod * math.sin(radian)), -round(mod * math.cos(radian))


def max_f(a, b):
	if a > b:
		return a
	else:
		return b


def min_f(a, b):
	if a < b:
		return a
	else:
		return b


if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = WindowWidget()
	window.show()
	window.load_image('res/image2.jpg')
	sys.exit(app.exec_())
