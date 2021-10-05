# coding=utf-8

import math
import os
import sys
import time

import pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt5
import pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt5
import pyqtgraph.imageview.ImageViewTemplate_pyqt5
import numpy as np
from pyqtgraph import Vector
from pyqtgraph.opengl import GLViewWidget, GLTextItem, GLAxisItem, GLGridItem, GLScatterPlotItem
from PyQt5.QtCore import QStandardPaths, QSettings, QFile, pyqtSlot, Qt
from PyQt5.QtGui import QImage, QPixmap, QIcon, QKeySequence, QColor, QFont
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QShortcut, QFileDialog, QApplication, QStackedLayout

WINDOW_TITLE = '图像-色彩分析器'
WINDOW_SIZE = (634, 950)
IMAGE_SIZE = (610, 300)
IMAGE_HEIGHT_MAX = 610
INFO_SIZE = (150, 20)
POINT_RADIUS = 10
SCOPE_SIZE = (300, 300)
SCOPE_RADIUS = int(SCOPE_SIZE[0] / 2)
SCOPE_BAR = 20
SCOPE_3D_SIZE = (604, 300)
SCOPE_3D_MOVE = (17, 634)
SCOPE_3D_X = 10
SCOPE_3D_X_H = SCOPE_3D_X / 2
SCOPE_3D_Y = 10
SCOPE_3D_Y_H = SCOPE_3D_Y / 2
SCOPE_3D_L = 4
ANALYSE_POINTS = 20000
SCALE_MAX = 6
SCALE_STEP = 0.12


class WindowWidget(QWidget):
	def __init__(self):
		super(WindowWidget, self).__init__()
		self.label_image = None
		self.image_image = None
		self.pixmap = None
		self.image_set = False
		self.label_scope1 = None  # 波形示波器
		self.info_scope1 = None
		self.point_scope1 = None
		self.stack_scope1 = None
		self.image_scope1 = None
		self.label_scope2 = None  # 矢量示波器
		self.info_scope2 = None
		self.point_scope2 = None
		self.stack_scope2 = None
		self.image_scope2 = None
		self.scope_3d = None
		self.scope_3d_points = None
		self.scope_3d_ball = None
		self.settings = None
		self.mouse_press = set()
		self.setAcceptDrops(True)
		self.init_ui()
		self.reg_shortcut()
		self.init_setting()

	# ↓↓ init layout & widget
	def init_ui(self):
		self.init_scopes()

		self.image_image = QImage(res_path('res/empty.jpg'))
		self.label_image = QLabel(self)
		self.label_image.setFixedSize(*IMAGE_SIZE)
		self.label_image.setAlignment(Qt.AlignCenter)
		self.label_image.setStyleSheet('border: 1px solid #606060')
		self.label_image.setPixmap(QPixmap(self.image_image))

		# scope
		self.label_scope1 = QLabel(self)
		self.label_scope1.setFixedSize(*SCOPE_SIZE)
		self.label_scope1.setStyleSheet('border: 1px solid #606060')
		self.label_scope1.setPixmap(QPixmap(self.image_scope1))
		self.label_scope2 = QLabel(self)
		self.label_scope2.setFixedSize(*SCOPE_SIZE)
		self.label_scope2.setStyleSheet('border: 1px solid #606060')
		self.label_scope2.setPixmap(QPixmap(self.image_scope2))
		self.info_scope1, self.point_scope1, self.stack_scope1 = self.init_info(self.label_scope1)
		self.info_scope2, self.point_scope2, self.stack_scope2 = self.init_info(self.label_scope2)

		# layout
		layout = QVBoxLayout()
		layout.addWidget(self.label_image)
		layout_scopes = QHBoxLayout()
		layout_scopes.addLayout(self.stack_scope1)
		layout_scopes.addLayout(self.stack_scope2)
		layout.addLayout(layout_scopes)

		self.scope_3d = GLViewWidget(self)
		self.scope_3d.opts['center'] = Vector(0, 0, 1.2)
		self.scope_3d.opts['distance'] = 18
		self.scope_3d.opts['fov'] = 45
		self.scope_3d.opts['elevation'] = 10
		self.scope_3d.opts['azimuth'] = -90
		txt_zero = GLTextItem(pos=(-5, -5, 0), text='o', font=QFont('arial', 10), color=QColor('#404040'))
		txt_x = GLTextItem(pos=(5, -5, 0), text='x', font=QFont('arial', 10), color=QColor('#404040'))
		txt_y = GLTextItem(pos=(-5, 5, 0), text='y', font=QFont('arial', 10), color=QColor('#404040'))
		self.scope_3d.addItem(txt_zero)
		self.scope_3d.addItem(txt_x)
		self.scope_3d.addItem(txt_y)
		self.scope_3d.addItem(GLAxisItem())  # TODO remove
		g_floor = GLGridItem()
		g_floor.setSize(SCOPE_3D_X, SCOPE_3D_Y, 1)
		self.scope_3d.addItem(g_floor)
		g_light = GLGridItem()
		g_light.setSize(SCOPE_3D_X, SCOPE_3D_L, 1)
		g_light.setSpacing(SCOPE_3D_X, 1, 1)
		g_light.rotate(90, 1, 0, 0)
		g_light.translate(0, SCOPE_3D_Y / 2, SCOPE_3D_L / 2)
		self.scope_3d.addItem(g_light)
		self.scope_3d.resize(*SCOPE_3D_SIZE)
		self.scope_3d.move(*SCOPE_3D_MOVE)
		self.scope_3d.show()

		self.setLayout(layout)
		self.setFixedSize(*WINDOW_SIZE)
		self.setWindowTitle(WINDOW_TITLE)
		self.setStyleSheet('background-color: #303030')
		self.setWindowIcon(QIcon(res_path('res/ico.ico')))

	def init_info(self, label_scope):
		widget = QWidget(self)
		widget.setAttribute(Qt.WA_TranslucentBackground)
		info_scope = QLabel(widget)
		info_scope.setFixedSize(*INFO_SIZE)
		info_scope.move(1, 1)
		info_scope.setStyleSheet('background-color: #202020; font-family: arial; font-size: 10; color: #909090')
		point_scope = QLabel(widget)
		point_scope.setFixedSize(POINT_RADIUS * 2, POINT_RADIUS * 2)
		point_scope.setAttribute(Qt.WA_TranslucentBackground)
		point_scope.setPixmap(QPixmap(QImage(res_path('res/point.png'))))
		stack_scope = QStackedLayout()
		stack_scope.addWidget(label_scope)
		stack_scope.addWidget(widget)
		stack_scope.setCurrentIndex(0)
		stack_scope.setStackingMode(QStackedLayout.StackAll)
		return info_scope, point_scope, stack_scope

	def init_scopes(self):
		self.image_scope1 = QImage(res_path('res/scope1.jpg'))
		self.image_scope2 = QImage(res_path('res/scope2.jpg'))

	# ↓↓ reg shortcut
	def reg_shortcut(self):
		shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
		shortcut_open.activated.connect(self.on_open)
		shortcut_paste = QShortcut(QKeySequence("Ctrl+V"), self)
		shortcut_paste.activated.connect(self.paste_image)
		shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
		shortcut_save.activated.connect(self.save_window)

	# ↓↓ init setting
	def init_setting(self):
		local_dir = os.path.dirname(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
		setting_path = local_dir + '/image-scope/setting.ini'
		self.settings = QSettings(setting_path, QSettings.IniFormat)

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

	# ↓↓ mouse event
	def mousePressEvent(self, event):
		if event.button() == 1:
			self.mouse_press.add(1)
			self.show_pix_info(event.x(), event.y())

	def mouseReleaseEvent(self, event):
		if event.button() == 1:
			self.mouse_press.remove(1)
			self.hide_pix_info()
			self.scope_3d.raise_()

	def mouseMoveEvent(self, event):
		if 1 in self.mouse_press:
			self.show_pix_info(event.x(), event.y())

	def show_pix_info(self, x, y):
		if not self.image_set:
			return
		x = x - self.label_image.x() - int((IMAGE_SIZE[0] - self.pixmap.width()) / 2)
		y = y - self.label_image.y()
		if x < 0 or x >= self.pixmap.width():
			return
		if y < 0 or y >= self.pixmap.height():
			return
		color: QColor = self.pixmap.toImage().pixelColor(x, y)
		r_v, g_v, b_v = color.red(), color.green(), color.blue()
		h_v, s_v, l_v = color.hue(), color.saturation(), color.lightness()
		self.info_scope1.setText(' rgb: [{},{},{}]'.format(r_v, g_v, b_v))
		self.info_scope2.setText(' hsl: [{},{},{}]'.format(h_v, s_v, l_v))
		h_f, s_f, l_f = color.hueF(), color.saturationF(), color.lightnessF()
		scope_1_w = SCOPE_SIZE[0]
		scope_1_h = SCOPE_SIZE[1] - SCOPE_BAR
		x_1, y_1 = hl_2_xy(scope_1_w, scope_1_h, h_f, l_f)
		x_2, y_2 = hs_2_xy(SCOPE_RADIUS, h_f, s_f)
		self.point_scope1.move(x_1 - POINT_RADIUS, scope_1_h - y_1 - POINT_RADIUS)
		self.point_scope2.move(x_2 + SCOPE_RADIUS - POINT_RADIUS, y_2 + SCOPE_RADIUS - POINT_RADIUS)

		p = np.empty((4, 3))
		c = np.empty((4, 4))
		s = np.empty(1)
		s[0] = 16
		r_f, g_f, b_f = color.redF(), color.greenF(), color.blueF()
		w = self.pixmap.width()
		h = self.pixmap.height()
		wh_max = max(w, h)
		x_off = (wh_max - w) / 2 / wh_max
		y_off = (wh_max - h) / 2 / wh_max
		x_f = x / wh_max + x_off
		y_f = (h - y - 1) / wh_max + y_off
		p[0] = (SCOPE_3D_X * x_f - SCOPE_3D_X_H, SCOPE_3D_Y * y_f - SCOPE_3D_Y_H, SCOPE_3D_L * l_f)
		p[1] = (SCOPE_3D_X * x_f - SCOPE_3D_X_H, SCOPE_3D_Y * y_f - SCOPE_3D_Y_H, SCOPE_3D_L * r_f)
		p[2] = (SCOPE_3D_X * x_f - SCOPE_3D_X_H, SCOPE_3D_Y * y_f - SCOPE_3D_Y_H, SCOPE_3D_L * g_f)
		p[3] = (SCOPE_3D_X * x_f - SCOPE_3D_X_H, SCOPE_3D_Y * y_f - SCOPE_3D_Y_H, SCOPE_3D_L * b_f)
		c[0] = (1, 1, 1, 0.2)
		c[1] = (1, 1, 1, 0.2)
		c[2] = (1, 1, 1, 0.2)
		c[3] = (1, 1, 1, 0.2)
		ball_3d = GLScatterPlotItem(pos=p, color=c, size=s)
		if self.scope_3d_ball is not None:
			self.scope_3d.removeItem(self.scope_3d_ball)
		self.scope_3d_ball = ball_3d
		self.scope_3d.addItem(ball_3d)

		self.stack_scope1.setCurrentIndex(1)
		self.stack_scope2.setCurrentIndex(1)

	def hide_pix_info(self):
		if self.scope_3d_ball is not None:
			self.scope_3d.removeItem(self.scope_3d_ball)
			self.scope_3d_ball = None
		self.stack_scope1.setCurrentIndex(0)
		self.stack_scope2.setCurrentIndex(0)

	# ↓↓ open event
	@pyqtSlot()
	def on_open(self):
		last_path = self.settings.value('open_path', '.')
		file = QFileDialog.getOpenFileName(self, '打开图像文件', last_path, '*.jpg;*.png;*.jpeg;*.bmp')
		if file[0]:
			self.settings.setValue('open_path', os.path.dirname(file[0]))
			self.load_image(file[0])

	# ↓↓ paste event
	@pyqtSlot()
	def paste_image(self):
		image = QApplication.clipboard().pixmap().toImage()
		if not image.isNull():
			self.image_image = image
			self.refresh_image()

	# ↓↓ save event
	@pyqtSlot()
	def save_window(self):
		if not self.image_set:
			return
		screen = QApplication.primaryScreen()
		screenshot = screen.grabWindow(self.winId())
		last_path = self.settings.value('save_path', '.')
		default_name = 'image-scope_' + time.strftime('%Y%m%d%H%M%S', time.localtime()) + '.jpg'
		file = QFileDialog.getSaveFileName(self, '保存示波器图片', last_path + '/' + default_name, '*.jpg')
		self.settings.setValue('save_path', os.path.dirname(file[0]))
		screenshot.save(QFile(file[0]))

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
		pl_points = []
		w = self.image_image.width()
		h = self.image_image.height()

		# 分析像素
		jump = max(1, round(math.sqrt(w * h / ANALYSE_POINTS)))
		for x in range(0, w, jump):
			for y in range(0, h, jump):
				color: QColor = self.image_image.pixelColor(x, y)
				h_f, s_f, l_f = color.hueF(), color.saturationF(), color.lightnessF()
				r_f, g_f, b_f = color.redF(), color.greenF(), color.blueF()
				x_hl, y_hl = hl_2_xy(hl_w, hl_h, h_f, l_f)
				x_hs, y_hs = hs_2_xy(SCOPE_RADIUS, h_f, s_f)
				if (x_hl, y_hl) not in hl_points:
					hl_points[(x_hl, y_hl)] = color
				if (x_hs, y_hs) not in hs_points:
					hs_points[(x_hs, y_hs)] = color
				pl_points.append((x, h - y - 1, l_f, r_f, g_f, b_f))

		# 波形示波器（x-色相，y-亮度）
		for pos, color in hl_points.items():
			c = QColor()
			c.setHsl(color.hslHue(), 200, int(color.lightness() * 0.9 + 24))
			self.image_scope1.setPixelColor(pos[0], hl_h - pos[1], c)

		# 矢量示波器
		for pos, color in hs_points.items():
			c = QColor()
			c.setHsv(color.hsvHue(), color.hsvSaturation(), 255)
			self.image_scope2.setPixelColor(pos[0] + SCOPE_RADIUS, pos[1] + SCOPE_RADIUS, c)

		# 分量图
		p = np.empty((len(pl_points) * 4, 3))
		c = np.empty((len(pl_points) * 4, 4))
		s = np.empty(1)
		s[0] = 1
		wh_max = max(w, h)
		x_off = (wh_max - w) / 2 / wh_max
		y_off = (wh_max - h) / 2 / wh_max
		for i in range(len(pl_points)):
			x, y, l_f, r_f, g_f, b_f = pl_points[i]
			x_f = x / wh_max + x_off
			y_f = y / wh_max + y_off
			p[i * 4 + 0] = (SCOPE_3D_X * x_f - SCOPE_3D_X_H, SCOPE_3D_Y * y_f - SCOPE_3D_Y_H, SCOPE_3D_L * l_f)
			p[i * 4 + 1] = (SCOPE_3D_X * x_f - SCOPE_3D_X_H, SCOPE_3D_Y * y_f - SCOPE_3D_Y_H, SCOPE_3D_L * r_f)
			p[i * 4 + 2] = (SCOPE_3D_X * x_f - SCOPE_3D_X_H, SCOPE_3D_Y * y_f - SCOPE_3D_Y_H, SCOPE_3D_L * g_f)
			p[i * 4 + 3] = (SCOPE_3D_X * x_f - SCOPE_3D_X_H, SCOPE_3D_Y * y_f - SCOPE_3D_Y_H, SCOPE_3D_L * b_f)
			c[i * 4 + 0] = (1, 1, 1, l_f * 0.5 + 0.5)
			c[i * 4 + 1] = (1, 0, 0, r_f * 0.5 + 0.5)
			c[i * 4 + 2] = (0, 1, 0, g_f * 0.5 + 0.5)
			c[i * 4 + 3] = (0, 0, 1, b_f * 0.5 + 0.5)
		points_3d = GLScatterPlotItem(pos=p, color=c, size=s)
		if self.scope_3d_points is not None:
			self.scope_3d.removeItem(self.scope_3d_points)
		self.scope_3d_points = points_3d
		self.scope_3d.addItem(points_3d)

		self.image_set = True
		self.resize_window()
		self.pixmap = QPixmap(self.image_image).scaled(IMAGE_SIZE[0], self.label_image.height(), Qt.KeepAspectRatio)
		self.label_image.setPixmap(self.pixmap)
		self.label_scope1.setPixmap(QPixmap(self.image_scope1))
		self.label_scope2.setPixmap(QPixmap(self.image_scope2))

	def resize_window(self):
		image_h = int(IMAGE_SIZE[0] / self.image_image.width() * self.image_image.height())
		image_h = min(IMAGE_HEIGHT_MAX, image_h)
		new_h = image_h - IMAGE_SIZE[1] + WINDOW_SIZE[1]
		self.setFixedSize(WINDOW_SIZE[0], new_h)
		self.scope_3d.move(SCOPE_3D_MOVE[0], new_h - (WINDOW_SIZE[1] - SCOPE_3D_MOVE[1]))
		self.label_image.setFixedSize(IMAGE_SIZE[0], image_h)


def hl_2_xy(w, h, h_f, l_f):
	return round(w * h_f), round(h * l_f)


def hs_2_xy(r, h_f, s_f):
	# to match with DaVinci vector-scope, make a little rotation
	radian = 2 * math.pi * h_f + math.pi * 0.12
	mod = r * s_f
	return -round(mod * math.sin(radian)), -round(mod * math.cos(radian))


def res_path(path):
	if hasattr(sys, '_MEIPASS'):
		return getattr(sys, '_MEIPASS') + '/' + path
	else:
		return path


if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = WindowWidget()
	window.show()
	sys.exit(app.exec_())
