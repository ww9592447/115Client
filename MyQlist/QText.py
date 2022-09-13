from .package import MyQLabel, ClickQLabel, picture, QLabel, QApplication, Qt, QPixmap, QFont, QMenu, QCursor, QMetaMethod
# from bisect import bisect_left


class MyLText(MyQLabel):
	def __init__(self, parent, size=11):
		super().__init__(parent)
		# 所有信號
		self.signal = {'leftclick': [], 'doubleclick': [], 'qss': False}
		# 保存所有文字
		self.text_ = None
		# 保存原本寬度
		self.width_ = 0
		# 文字最大大小
		self.textmax = 0
		# 記錄所有文字分別大小
		self.textsize = []
		# 間隔符號
		self.spacersymbol = '...'
		# 獲取字體設置
		font = QFont()
		# 設置字體大小
		font.setPointSize(size)
		# 設定標題字體大小
		self.setFont(font)
		# 間隔符號大小
		self.spacersymbolsize = self.fontMetrics().horizontalAdvance(self.spacersymbol)
		# 間隔空白
		self.spacedblank = 5
		# 空白總大小
		self.spacedblanksize = self.fontMetrics().horizontalAdvance(' ') * self.spacedblank

	# 單擊
	def mousePressEvent(self, event):
		MyQLabel.mousePressEvent(self, event)
		# 讓事件繼續往上傳遞  為了 不影響 左鍵點擊事件
		event.ignore()

	# 設定文字
	def settext(self, text):
		width = self.width_
		if text != self.text_:
			# 保存完整文字
			self.text_ = text
			# 文字所有大小清空
			self.textsize = []
			# 獲取 計算文字寬度函數
			horizontaladvance = self.fontMetrics().horizontalAdvance
			# 設定最大文字寬度大小
			self.textmax = horizontaladvance(text)
			# 設置可調整的最大寬度
			self.setMaximumWidth(self.textmax)
			# 初始化文字大小
			size = 0
			# 循環獲取文字大小 文字位置
			for _text, index in zip(text, range(len(text))):
				# 獲取文字大小
				size = size + horizontaladvance(_text)
				# 添加文字大小 位置
				self.textsize.append((index + 1, size))
			# 文字大小翻轉 重大到小
			self.textsize.reverse()
		# 查看文字大小 + 間隔空白大小 是否大於 寬度 如果大於設定新文字
		if self.textmax + self.spacedblanksize > width:
			# 獲取文字大小
			for index, size in self.textsize:
				# 查看目前文字大小 + 間隔符號大小 + 間隔空白大小 是否小於寬度 如果小於就重新設定文字
				if size + self.spacersymbolsize + self.spacedblanksize < width:
					# 設定文字
					text = self.text_[0:index] + self.spacersymbol
					# 獲取文字大小
					width = size + self.spacersymbolsize
					break
		# 如果文字不同就設置新文字
		if self.text() != text:
			# 設定文字
			QLabel.setText(self, text)
		return width

	# 接收標題發送的信號
	def setdata(self, s, x, width):
		if s == 'resize':
			self.resize(x + width - self.x(), self.height())
		else:
			self.move(x, self.y())

	# 手動更新文字
	def update_(self, text):
		# 設定文字 並獲得文字大小
		width = self.settext(text)
		QLabel.resize(self, width, self.height())

	# 覆蓋 resize 事件
	def resize(self, *event):
		# 保存原本寬度
		self.width_ = event[0]
		# 設定文字 並獲得文字大小
		width = self.settext(self.text_)
		# 設置文字大小
		QLabel.resize(self, width, event[1])


class Text(MyQLabel):
	def __init__(self, text=None, listcheck=None, data=None, ico=None, my_mode=None, text_mode=None):
		super().__init__(None)
		self.setStyleSheet(
			'Text{background-color: white}'
			'Text:hover{background-color: rgb(249, 250, 251)}'
			'Text[status="true"]{background-color: rgb(234, 246, 253)}'
		)
		self.listcheck = listcheck
		# 所有信號
		self.signal = {'leftclick': [], 'doubleclick': []}
		# 設定選中狀態qss屬性
		self.setProperty('status', False)
		# 設定按鍵發射
		self.slot = self
		# 點擊狀態
		self.status = False
		# text圖標
		self.textico = None
		# 紀錄text圖標文字
		self.ico = None
		# 右鍵
		self.contextMenu = None
		# 紀錄本身資料
		self.text_data = {'text': text, 'mode': text_mode, '_mode': None}
		self.my_data = {'ico': ico, 'mode': my_mode, '_mode': None}
		# 記錄額外資料
		self.data = data
		# 所有text
		self.alltext = {}
		# 設定複選按鈕
		self.checkbutton = ClickQLabel(self)
		# 設定複選按鈕發射信息
		self.checkbutton.slot = self
		# 查看複選按鈕是否需要手動更改大小
		if self.listcheck.touchable:
			# 手動設置複選按鈕大小
			self.checkbutton.resize(*self.listcheck.touchable)
			# 把複選鈕置中
			self.checkbutton.move(5, int((self.listcheck.textmax - self.checkbutton.height()) / 2))
		else:
			# 把複選鈕置中
			self.checkbutton.move(5, int((self.listcheck.textmax - self.checkbutton.height()) / 2))
		# 刷新子text資料
		self.refresh()

	# 重新設定子texts資料
	def setdata(self, text=None, data=None, ico=None, my_mode=None, text_mode=None):
		self.text_data = {'text': text, 'mode': text_mode, '_mode': None}
		self.my_data = {'ico': ico, 'mode': my_mode, '_mode': None}
		self.data = data
		self.refresh()

	# 設定 子text 相關資料
	def refresh(self):
		# 查看是否需要設定圖標
		if self.my_data['ico'] is not None and self.ico != self.my_data['ico']:
			# 獲取相應圖標
			_ico = picture(self.my_data['ico'])
			# 保存目前的圖標文字
			self.ico = self.my_data['ico']
			# 設定圖標
			self.textico = QLabel(self)
			# 設定圖標圖片
			self.textico.setPixmap(_ico)
			# 設置圖標大小
			self.textico.resize(_ico.size())
			# 設置圖標位置
			self.textico.move(
				self.checkbutton.x() + self.checkbutton.width() + 10,
				int((self.listcheck.textmax - self.textico.height()) / 2)
			)
		# 查看 是否需要單獨設定 點擊信號 顏色
		if self.my_data['mode'] != self.my_data['_mode']:
			# 查看 自身 是否需要設定單擊信號
			if 'leftclick' in self.my_data['mode']:
				for mode in self.my_data['mode']['leftclick']:
					# 查看是否重複連接 不重複則進入
					if mode not in self.signal['leftclick']:
						# 連接自身左鍵點擊信號
						self.leftclick.connect(mode)
						# 所有信號添加信號
						self.signal['leftclick'].append(mode)
			# 查看 自身 是否需要設定雙擊信號
			if 'doubleclick' in self.my_data['mode']:
				for mode in self.my_data['mode']['doubleclick']:
					# 查看是否重複連接 不重複則進入
					if mode not in self.signal['doubleclick']:
						# 連接自身左鍵雙擊信號
						self.doubleclick.connect(mode)
						# 所有信號添加信號
						self.signal['doubleclick'].append(mode)
			# 紀錄 自身 資料 為了下次更新 如果沒變化就不用進來了
			self.my_data['_mode'] = self.my_data['mode']
		# 獲取text資料
		text = self.text_data['text']
		# 循環所有標題
		for name in self.listcheck.alltitle:
			# 獲取標題
			title = name.data[0]
			# 替換已有的text
			if name in self.alltext and name in text and text[name] != self.alltext[name].text_:
				# 獲取之前的text
				_text = self.alltext[name]
				# text更新成新文字
				self.alltext[name].update_(text[name])
			# 如果 全部符合 就 獲取 self.alltext 的 name
			elif name in self.alltext and name in text and text[name] == self.alltext[name].text_:
				_text = self.alltext[name]
			# 如果 text裡 沒有 符合標題的  添加新的text
			elif name not in self.alltext and name in text:
				# 新增空白text
				_text = MyLText(self)
				# 空白text更新文字
				_text.update_(text[name])
			# 新增空
			elif name not in text:
				if name in self.alltext:
					_text = self.alltext[name]
				else:
					_text = MyLText(self)
				_text.update_('-')
			else:
				continue
			# 查看 是否需要單獨設定 點擊信號 顏色
			if self.text_data['mode'] != self.text_data['_mode']:
				# 查看 text 是否需要設定標題 顏色
				if name in self.text_data['mode']:
					# 查看 text 是否需要設定單擊信號
					if 'leftclick' in self.text_data['mode'][name]:
						for mode in self.text_data['mode'][name]['leftclick']:
							# 查看是否重複連接 不重複則進入
							if mode not in _text.signal['leftclick']:
								# 連接text左鍵點擊信號
								_text.leftclick.connect(mode)
								# text 所有信號添加信號
								_text.signal['leftclick'].append(mode)
						# 滑鼠設定成可點擊圖標
						_text.setCursor(Qt.PointingHandCursor)
					# 查看 text 是否需要設定標題 顏色
					if 'color' in self.text_data['mode'][name] and not _text.signal['qss']:
						# 設定QSS 預設顏色 移動到上方顏色
						_text.setStyleSheet(
							f'MyLText{{color: rgb{self.text_data["mode"][name]["color"][0]}}}'
							f'MyLText:hover{{color: rgb{self.text_data["mode"][name]["color"][1]}}}'
							)
			# 獲取 y座標
			y = int((self.listcheck.textmax - _text.fontMetrics().height()) / 2)
			if self.listcheck.alltitle.index(name) == 0 and self.textico:
				# 獲取子Text x位置
				x = self.textico.x() + self.textico.width() + 10
				# 設定子Text 座標
				_text.move(x, y)
				# 設定子Text 大小
				_text.resize(title.x() + title.width() - x, _text.fontMetrics().height())
			else:
				# 設定子Text 座標
				_text.move(title.x(), y)
				# 設定子Text 大小
				_text.resize(title.width(), _text.fontMetrics().height())
			_text.show()
			if name not in self.alltext:
				# 新增到所有text內
				self.alltext[name] = _text
		# 紀錄 text 資料 為了下次更新 如果沒變化就不用進來了
		self.text_data['_mode'] = self.text_data['mode']
		# 查看所有 text 是否有多餘的 如果有則刪除
		for name in set(self.alltext.keys()) ^ set(self.listcheck.alltitle):
			self.alltext[name].setParent(None)
			self.alltext[name].deleteLater()
			self.alltext.pop(name)

	# 右鍵菜單事件
	def menuclick(self, text, slot, mode=True):
		# 在右鍵位置顯示
		def display():
			if self.listcheck.menu_callback:
				self.listcheck.menu_callback(lambda: self.contextMenu.popup(QCursor.pos()))
			else:
				self.contextMenu.popup(QCursor.pos())
				# for _, values in self.listcheck.menu.items():
				# 	for _, _values in values.items():
				# 		if _values.isVisible():
				# 			self.contextMenu.popup(QCursor.pos())
				# 			return

		# 如果沒有QMenu信號事件 創建QMenu信號事件
		if self.contextMenu is None:
			self.setContextMenuPolicy(Qt.CustomContextMenu)
			self.customContextMenuRequested.connect(display)
			self.contextMenu = QMenu(self)

		cp = self.contextMenu.addAction(text)
		cp.triggered.connect(slot)
		cp.setVisible(mode)
		if self not in self.listcheck.menu:
			self.listcheck.menu[self.listcheck.page][self] = {text: cp}
		else:
			self.listcheck.menu[self.listcheck.page][self].update({text: cp})

	# 設定選中狀態
	def setstatus(self, status=None):
		# 查看使否需要自動設定複選紐
		if not status:
			# 獲取點擊後的複選紐狀態
			status = not self.property('status')
		# 設定複選紐 成相應 狀態
		self.checkbutton.setimage(status)
		if status:
			self.listcheck.currentclick.append(self)
		else:
			self.listcheck.currentclick.remove(self)
		# 設置本身狀態
		self.status = status
		# 設定背景顏色
		self.setProperty('status', status)
		# 刷新QSS
		self.setStyle(self.style())
		# 返回目前點擊的狀態
		return status


class QText:
	def __init__(self, listcheck):
		self.listcheck = listcheck

	# 添加一個列表 *args 文字列表 data 額外資料 ico 圖標 mode 文字點擊事件 顏色 設定
	def add(self, text, index=None, data=None, ico=None, my_mode=None, text_mode=None):
		if index:
			category = 1
		else:
			category = 0
		self._create(text, index=index, category=category, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)

	# 插入一個列表
	def insert(self, index, text, data=None, ico=None, my_mode=None, text_mode=None):
		self._create(text, category=2, index=index, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)

	def _create(self, text, category, index=None, data=None, ico=None, my_mode=None, text_mode=None):
		# 新增texts
		texts = Text(
			text, listcheck=self.listcheck, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode
		)
		# 查看是否需要新增
		if category == 0:
			page = 0
			for page in range(len(self.listcheck.alllist)):
				if len(self.listcheck.alllist[page]) + 1 <= self.listcheck.pagemax:
					break
			if len(self.listcheck.alllist[page]) + 1 > self.listcheck.pagemax:
				self.listcheck.quantity.add()
				page += 1
			texts.setParent(self.listcheck.scrollcontents[page])
			# 設置位置
			texts.setGeometry(
				0, len(self.listcheck.alllist[page]) * self.listcheck.textmax,
				self.listcheck.scrollcontents[page].width(), self.listcheck.textmax
			)
			# 添加新label
			self.listcheck.alllist[page].append(texts)
			index = page
		# 查看是否需要從 page頁 開始新增
		elif category == 1:
			page = len(self.listcheck.alllist) - 1
			for page in range(index, len(self.listcheck.alllist)):
				if len(self.listcheck.alllist[page]) < self.listcheck.pagemax:
					break
			if len(self.listcheck.alllist[page]) > self.listcheck.pagemax:
				self.listcheck.quantity.add()
				page += 1
			texts.setParent(self.listcheck.scrollcontents[page])
			# 設置位置
			texts.setGeometry(
				0, len(self.listcheck.alllist[page]) * self.listcheck.textmax,
				self.listcheck.scrollcontents[page].width(), self.listcheck.textmax
			)
			# 添加新label
			self.listcheck.alllist[page].append(texts)

		# 查看是否需要插入
		elif category == 2:
			insert_index = index // self.listcheck.pagemax
			_insert_index = index % self.listcheck.pagemax
			if insert_index + 1 > len(self.listcheck.alllist):
				self._create(texts, index=insert_index, category=1, data=data, ico=ico, my_mode=my_mode, text_mode=text_mode)
				return

			while 1:
				texts.setParent(self.listcheck.scrollcontents[insert_index])
				alllist = self.listcheck.alllist[insert_index]
				alllist.insert(_insert_index, texts)
				for _texts, _index in zip(alllist, range(len(alllist))):
					_texts.setGeometry(
						0, _index * self.listcheck.textmax,
						self.listcheck.scrollcontents[insert_index].width(), self.listcheck.textmax
					)
				if len(self.listcheck.alllist[insert_index]) > self.listcheck.pagemax:
					texts = self.listcheck.alllist[insert_index].pop()
					_insert_index = 0
					insert_index += 1
					if insert_index > len(self.listcheck.alllist) - 1:
						self.listcheck.quantity.add()
				else:
					break
		# texts顯示
		texts.show()
		# vbox 點擊初始化
		texts.checkbutton.leftclick.connect(self._vbox_left_select)
		texts.checkbutton.rightclick.connect(self._vbox_right_select)
		# texts 點擊初始化
		texts.leftclick.connect(self._text_left_select)
		texts.rightclick.connect(self._text_right_select)

		# 初始化點擊事件
		for slot in self.listcheck.click_connect:
			if slot[0] == 'texts':
				getattr(texts, slot[1]).connect(slot[2])
			elif slot[0] == 'menu':
				getattr(texts, slot[1])(slot[2], slot[3])
		if self.listcheck.page != index:
			return
		elif self.listcheck.title.clickqlabel.status:
			self.listcheck.title.clickqlabel.setstatus(False)
		elif not self.listcheck.currentclick:
			self.listcheck.quantity.all(len(self.listcheck.alllist[self.listcheck.page]))
		# 設置內容容器大小
		self.listcheck.scrollcontents[self.listcheck.page].resize(
			self.listcheck.scrollcontents[self.listcheck.page].width(),
			len(self.listcheck.alllist[self.listcheck.page]) * self.listcheck.textmax
		)

	# 複選紐左鍵點擊事件
	def _vbox_left_select(self, texts):
		# 點著shift事件
		if QApplication.keyboardModifiers() == Qt.ShiftModifier:
			self._shift(texts)
			return
		# 設定成最後一次點擊
		self.listcheck.firstclick = texts
		texts.setstatus()

	# 複選紐右擊點擊事件
	def _vbox_right_select(self, texts):
		# 設定成最後一次點擊
		self.listcheck.firstclick = texts
		texts.setstatus()

	# texts左鍵單擊點擊事件
	def _text_left_select(self, texts):
		# CTRL事件
		if QApplication.keyboardModifiers() == Qt.ControlModifier:
			self._vbox_left_select(texts)
			return
		# SHIFT事件
		if QApplication.keyboardModifiers() == Qt.ShiftModifier:
			self._shift(texts)
		else:
			self._radio(texts)

	# label右擊點擊事件
	def _text_right_select(self, texts):
		if texts.status:
			return
		# CTRL事件
		if QApplication.keyboardModifiers() == Qt.ControlModifier:
			self._vbox_left_select(texts)
			return
		# SHIFT事件
		if QApplication.keyboardModifiers() == Qt.ShiftModifier:
			self._shift(texts)
		else:
			self._radio(texts)

	# 單獨選一個
	def _radio(self, texts):
		self.listcheck.firstclick = texts
		# 獲得已點擊複製
		currentclick = self.listcheck.currentclick.copy()
		if texts in currentclick:
			currentclick.remove(texts)
		else:
			texts.setstatus()
		for _texts in currentclick:
			_texts.setstatus()

	# shift事件
	def _shift(self, texts):
		alllist = self.listcheck.alllist[self.listcheck.page]
		# 獲取目前點擊的texts 是在第幾個
		index = alllist.index(texts)
		# 查看最後一次點擊 之前是否點擊過
		if self.listcheck.firstclick is not None:
			_index = alllist.index(self.listcheck.firstclick)
			# 獲取目前點擊的 - 最後點擊 之間的數量
			multiple_selection = index - _index
			# 查看數量是否大於0
			if multiple_selection > 0:
				currently = alllist[_index:index + 1]
			# 查看數量是否小於0
			elif multiple_selection < 0:
				currently = alllist[index:_index + 1]
			# 如果等於0進入點擊
			else:
				# 進入單獨點擊
				self._radio(texts)
				return
			# 獲取目前所有以點擊的複製
			currentclick = self.listcheck.currentclick.copy()
			# 循環舊的所有texts 複製
			for texts in currentclick:
				# 查看 index 是否在新典籍範圍之內
				if texts in currently:
					# 在點擊範圍之內 就移除新點擊範圍的 index 不需要重新設定複選紐
					currently.remove(texts)
				else:
					# 在點擊範圍之外 設定成空複選紐
					texts.setstatus()
			# 循環新的所有texts點擊
			for texts in currently:
				# 設定成選中複選紐
				texts.setstatus()
		else:
			self.listcheck.firstclick = texts
			self._radio(texts)