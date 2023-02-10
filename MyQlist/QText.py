from .module import MyQLabel, MyQFrame, Callable, ClickQLabel, picture, QLabel, QSize, QApplication, Qt, QFont, QMenu, QCursor,\
	Optional, QMouseEvent, MyTextSave, QFontMetrics

if False:
	from QList import ListCheck
	from QTitle import Title


class Text(MyQFrame):
	def __init__(
			self, listcheck: 'ListCheck', index: int,
			text_left_select: Callable[['Text'], None], text_right_select: Callable[['Text'], None]
	) -> None:
		super(Text, self).__init__(listcheck.scrollcontents)
		self.listcheck: ListCheck = listcheck
		# text左鍵單擊點擊事件
		self.text_left_select: Callable[[Text], None] = text_left_select
		# text右鍵單擊點擊事件
		self.text_right_select: Callable[[Text], None] = text_right_select
		# 自身編號
		self.index = index
		# 點擊狀態
		self.state: bool = False
		# 設定按鍵發射
		self.slot: Text = self
		# text圖標
		self.icoimage: QLabel = QLabel(self)
		# text圖標 隱藏
		self.icoimage.hide()
		# 設定 第一個子text x座標位置
		self.text_x = 0
		# 獲取字體設置
		font: QFont = QFont()
		# 設置字體大小
		font.setPointSize(11)
		# 獲取 子text y座標 位置
		self._y = int((self.listcheck.textmax - QFontMetrics(font).height()) / 2)
		# 紀錄text圖標文字
		self._ico: str = ''
		# 紀錄 背景左鍵 點擊信號
		self._leftclick: list[Callable, ...] = []
		# 紀錄 背景左鍵 雙擊信號
		self._doubleclick: list[Callable, ...] = []
		# 記錄額外資料
		self.data: any = None
		# 記錄所有子text
		self.textlist: dict[str, MyText] = {}
		# # 初始化子text
		# for title in self.listcheck.titlelist.text():
		# 	# 新增空白text
		# 	self.textlist[title] = MyText(self)
		# 設定複選按鈕
		self.checkbutton: ClickQLabel = ClickQLabel(self)
		# 設定複選按鈕發射信息
		self.checkbutton.slot = self
		# 查看複選按鈕是否需要手動更改大小
		if self.listcheck.touchable:
			# 手動設置複選按鈕大小
			self.checkbutton.resize(*self.listcheck.touchable)
		# 把複選鈕置中
		self.checkbutton.move(5, int((self.listcheck.textmax - self.checkbutton.height()) / 2))
		# 設置右鍵菜單
		self.contextMenu: QMenu = QMenu(self)
		# 設置右鍵策略
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		# 設置右鍵連接事件
		self.customContextMenuRequested.connect(self.display)
		# 設定選中狀態qss屬性
		self.setProperty('state', False)
		# 設置 qss
		self.setStyleSheet(
			'Text{background-color: white}'
			'Text:hover{background-color: rgb(249, 250, 251)}'
			'Text[state="true"]{background-color: rgb(234, 246, 253)}'
		)

	# 滑鼠單擊事件
	def mousePressEvent(self, event: QMouseEvent) -> None:
		# 左鍵
		if event.buttons() == Qt.LeftButton:
			self.text_left_select(self)
		# 右鍵
		elif event.buttons() == Qt.RightButton:
			self.text_right_select(self)
		MyQFrame.mousePressEvent(self, event)

	# 設定 or 新增 子text 之後 並移動位子
	def settext(self, title: 'Title') -> None:
		if title.text in self.textlist:
			mytext = self.textlist[title.text]
		else:
			# 獲取空白text
			mytext = MyText(self)
			# 新增空白text
			self.textlist[title.text] = mytext

		if self.listcheck.titlelist.index(title.text) == 0 and not self.icoimage.isHidden():
			# 獲取子Text x位置
			x = self.icoimage.x() + self.icoimage.width() + 10
			# 設置第一個 子text x位置
			self.text_x = x
			# 設定子Text 座標
			mytext.move(x, self._y)
			# 設定子Text 大小
			mytext.resize(title.x() + title.width() - x, mytext.fontMetrics().height())
		else:
			# 設定子Text 座標
			mytext.move(title.x(), self._y)
			# 設定子Text 大小
			mytext.resize(title.width(), mytext.fontMetrics().height())

	# 重新設定子texts資料
	def refresh(self):
		save = self.listcheck.textsave[self.index]
		self.data = save['data']
		if save['ico'] and self._ico != save['ico']:
			# 獲取相應圖標
			ico = picture(save['ico'])
			# 保存目前的圖標文字
			self._ico = save['ico']
			# 設定圖標圖片
			self.icoimage.setPixmap(ico)
			# 設置圖標大小
			self.icoimage.resize(ico.size())
			# 設置圖標位置
			self.icoimage.move(
				self.checkbutton.x() + self.checkbutton.width() + 10,
				int((self.listcheck.textmax - self.icoimage.height()) / 2)
			)
			# 圖標顯示
			self.icoimage.show()
		elif save['ico'] is None and self.icoimage.isVisible():
			self._ico = None
			self.icoimage.hide()

		# 查看目前是否有左鍵點擊信號 如果有 則全部解除
		if self._leftclick:
			# 全部解除 左鍵點擊信號
			self.leftclick.disconnect()
			# 清空 左鍵信號
			self._leftclick.clear()

		# 查看目前是否有左鍵點擊信號 如果有 則全部解除
		if self._doubleclick:
			# 全部解除 左鍵點擊信號
			self.doubleclick.disconnect()
			# 清空 左鍵信號
			self._doubleclick.clear()

		if save['leftclick']:
			# 連接 新的 左鍵點擊信號
			for slot in save['leftclick']:
				self.leftclick.connect(slot)
				self._leftclick.append(slot)
		if save['doubleclick']:
			# 連接 新的 左鍵雙擊信號
			for slot in save['doubleclick']:
				self.doubleclick.connect(slot)
				self._doubleclick.append(slot)

		# 循環所有標題文字
		for name, title in self.listcheck.titlelist.title():
			mytext = self.textlist[name]
			if name in save['text']:
				data = save['text'][name]
			else:
				data = {'text': '-', 'leftclick': None, 'color': None}
			mytext.refresh(data)
			self.settext(title)

	# 右鍵事件
	def display(self):
		if self.listcheck.menu:
			if self.listcheck.menu_callback:
				self.listcheck.menu_callback(lambda: self.listcheck.contextmenu.exec_(QCursor.pos()))
			else:
				self.listcheck.contextmenu.exec_(QCursor.pos())

	# 設定選中狀態
	def setstate(self, state: Optional[bool] = None) -> None:
		# 查看使否需要自動設定複選紐
		if state is None:
			# 獲取點擊後的複選紐狀態
			state = not self.property('state')
		# 設定複選紐 成相應 狀態
		self.checkbutton.setimage(state)
		# 根據狀態 來進行 當前點擊列表 新增 刪除
		if state:
			self.listcheck.currentclick.append(self)
		else:
			self.listcheck.currentclick.remove(self)
		# 設置本身狀態
		self.state = state
		# 設定背景顏色
		self.setProperty('state', state)
		# 刷新QSS
		self.setStyle(self.style())
		# # 返回目前點擊的狀態
		# return state


class MyText(MyQLabel):
	def __init__(self, parent: Text) -> None:
		super(MyText, self).__init__(parent)
		# 保存 自身 數據
		self.data: MyTextSave = {'text': '', 'leftclick': None, 'color': None}
		# 紀錄 子text 左鍵點擊信號
		self._leftclick: list[Callable, ...] = []
		# 紀錄 子text qss滑動到上方顏色
		self._color: Optional[tuple[tuple[int, int, int], tuple[int, int, int]]] = None
		# 保存原本寬度
		self._width: int = 0
		# 文字最大大小
		self._textmax: int = 0
		# 記錄所有文字分別大小
		self.textsize: list[tuple[int, int]] = []
		# 間隔符號
		self._spacersymbol: str = '...'
		# 獲取字體設置
		font: QFont = QFont()
		# 設置字體大小
		font.setPointSize(11)
		# 設定 text 字體大小
		self.setFont(font)
		# 間隔符號大小
		self._spacersymbolsize = self.fontMetrics().horizontalAdvance(self._spacersymbol)
		# 間隔空白
		self._spacedblank: int = 5
		# 空白總大小
		self._spacedblanksize: int = self.fontMetrics().horizontalAdvance(' ') * self._spacedblank

	# 滑鼠單擊事件
	def mousePressEvent(self, event: QMouseEvent) -> None:
		# 左鍵
		if event.buttons() == Qt.LeftButton:
			self.parent().text_left_select(self.parent())
		# 右鍵
		elif event.buttons() == Qt.RightButton:
			self.parent().text_right_select(self.parent())
		MyQLabel.mousePressEvent(self, event)

	def refresh(self, data: MyTextSave):
		# 獲取text
		text = data['text']
		# 文字所有大小清空
		self.textsize.clear()
		# 獲取 計算文字寬度函數
		horizontaladvance = self.fontMetrics().horizontalAdvance
		# 設定最大文字寬度大小
		self._textmax = horizontaladvance(text)
		# 初始化文字大小
		size = 0
		# 循環獲取文字大小 文字位置
		for _text, index in zip(text, range(len(text))):
			# 獲取文字大小
			size = size + horizontaladvance(_text)
			# 添加文字大小 位置
			self.textsize.append((index + 1, size))
		# 文字大小翻轉 從大到小
		self.textsize.reverse()
		# 設置可調整的最大寬度
		self.setMaximumWidth(self._textmax)
		# 查看目前是否有左鍵點擊信號 如果有 則全部解除
		if self._leftclick:
			# 全部解除 左鍵點擊信號
			self.leftclick.disconnect()
			# 清空 左鍵信號
			self._leftclick.clear()
			# 如果沒有點擊信號
			if not data['leftclick']:
				# 滑鼠還原
				self.setCursor(Qt.ArrowCursor)

		if data['leftclick']:
			# 連接 新的 左鍵點擊信號
			for slot in data['leftclick']:
				self.leftclick.connect(slot)
				self._leftclick.append(slot)
			# 滑鼠設定成可點擊圖標
			self.setCursor(Qt.PointingHandCursor)
		if self.data['color'] != data['color'] and data['color']:
			# 設置text 預設顏色 滑動到上方顏色
			self.setStyleSheet(
				f'MyText{{color: rgb{data["color"][0]}}}'
				f'MyText:hover{{color: rgb{data["color"][1]}}}'
			)
		elif self.data['color'] and data['color'] is None:
			self.setStyleSheet('')
		# 更新數據
		self.data.update(**data)

	# 調整大小回調
	def resize(self, *event: int) -> None:
		if self.data:
			# 保存原本寬度
			self._width = event[0]
			# 初始化目前寬度
			width = event[0]
			# 獲取原本文字
			text = self.data['text']
			# 查看文字大小 + 間隔空白大小 是否大於 寬度 如果大於設定新文字
			if self._textmax + self._spacedblanksize > self._width:
				# 獲取文字大小
				for index, size in self.textsize:
					# 查看目前文字大小 + 間隔符號大小 + 間隔空白大小 是否小於寬度 如果小於就重新設定文字
					if size + self._spacersymbolsize + self._spacedblanksize < self._width:
						# 設定文字
						text = self.data['text'][0:index] + self._spacersymbol
						# 獲取文字大小
						width = size + self._spacersymbolsize
						break
			# 如果文字不同就設置新文字
			if self.text() != text:
				# 設定文字
				self.setText(text)
			# 調整大小
			QLabel.resize(self, width, event[1])


class QText:
	def __init__(self, listcheck: 'ListCheck'):
		self.listcheck: ListCheck = listcheck

		for index in range(self.listcheck.pagemax):
			text = Text(self.listcheck, index, self._text_left_select, self._text_right_select)
			# 設置位置
			text.setGeometry(
				0, len(self.listcheck.textlist) * self.listcheck.textmax,
				self.listcheck.scrollcontents.width(), self.listcheck.textmax
			)
			self.listcheck.textlist.append(text)
			# text顯示
			text.show()
			# vbox 點擊初始化
			text.checkbutton.leftclick.connect(self._vbox_left_select)
			text.checkbutton.rightclick.connect(self._vbox_right_select)
			# # texts 點擊初始化
			# text.leftclick.connect(self._text_left_select)
			# text.rightclick.connect(self._text_right_select)

	# 複選紐左鍵點擊事件
	def _vbox_left_select(self, text: Text) -> None:
		# 點著shift事件
		if QApplication.keyboardModifiers() == Qt.ShiftModifier:
			self._shift(text)
			return
		# 設定成最後一次點擊
		self.listcheck.firstclick = text
		text.setstate()

	# 複選紐右擊點擊事件
	def _vbox_right_select(self, text: Text) -> None:
		# 設定成最後一次點擊
		self.listcheck.firstclick = text
		text.setstate()

	# texts左鍵單擊點擊事件
	def _text_left_select(self, text: Text) -> None:
		# CTRL事件
		if QApplication.keyboardModifiers() == Qt.ControlModifier:
			self._vbox_left_select(text)
			return
		# SHIFT事件
		if QApplication.keyboardModifiers() == Qt.ShiftModifier:
			self._shift(text)
		else:
			self._radio(text)

	# label右擊點擊事件
	def _text_right_select(self, text: Text) -> None:
		if text.state:
			return
		# CTRL事件
		if QApplication.keyboardModifiers() == Qt.ControlModifier:
			self._vbox_left_select(text)
			return
		# SHIFT事件
		if QApplication.keyboardModifiers() == Qt.ShiftModifier:
			self._shift(text)
		else:
			self._radio(text)

	# 單獨選一個
	def _radio(self, text: Text) -> None:
		self.listcheck.firstclick = text
		# 獲得已點擊複製
		currentclick = self.listcheck.currentclick.copy()
		if text in currentclick:
			currentclick.remove(text)
		else:
			text.setstate()
		for _text in currentclick:
			_text.setstate()

	# shift事件
	def _shift(self, text: Text) -> None:
		# 獲取目前點擊的text 是在第幾個
		index = self.listcheck.textlist.index(text)
		# 查看最後一次點擊 之前是否點擊過
		if self.listcheck.firstclick is not None:
			_index = self.listcheck.textlist.index(self.listcheck.firstclick)
			# 獲取目前點擊的 - 最後點擊 之間的數量
			multiple_selection = index - _index
			# 查看數量是否大於0
			if multiple_selection > 0:
				currently = self.listcheck.textlist[_index:index + 1]
			# 查看數量是否小於0
			elif multiple_selection < 0:
				currently = self.listcheck.textlist[index:_index + 1]
			# 如果等於0進入點擊
			else:
				# 進入單獨點擊
				self._radio(text)
				return
			# 獲取目前所有以點擊的複製
			currentclick = self.listcheck.currentclick.copy()
			# 循環舊的所有text 複製
			for text in currentclick:
				# 查看 index 是否在新典籍範圍之內
				if text in currently:
					# 在點擊範圍之內 就移除新點擊範圍的 index 不需要重新設定複選紐
					currently.remove(text)
				else:
					# 在點擊範圍之外 設定成空複選紐
					text.setstate()
			# 循環新的所有texts點擊
			for text in currently:
				# 設定成選中複選紐
				text.setstate()
		else:
			self.listcheck.firstclick = text
			self._radio(text)



