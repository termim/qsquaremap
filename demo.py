"""
QSquareMap Demo
"""

import os
from pathlib import Path
import sys

os.environ['QT_API'] = 'pyqt6'

from qtpy.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QToolBar, QLabel, QStyle
from qtpy.QtGui import QIcon, QAction, QCursor
from qtpy.QtCore import QSize, Qt

from qsquaremap import Node, QSquareMap

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #self.setWindowIcon(QIcon('demo.png'))
        self.setGeometry(100, 100, 500, 300)

        self.setWindowTitle("QSquareMap Demo")

        self.setupUI()

        self.path = None
        self.count = 0
        self.filters = "Images (*.png *.jpg);;Vector (*.svg)"

        self.square_map = QSquareMap(self)
        self.square_map.highlightNode.connect(
            lambda n, p, m: self.process_event("Highlight", n, p, m))
        self.square_map.selectNode.connect(
            lambda n, p, m: self.process_event("Select", n, p, m))
        self.square_map.activateNode.connect(
            lambda n, p, m: self.process_event("Activate", n, p, m))

        self.load_model('.')
        self.setCentralWidget(self.square_map)
        self.show()


    def setupUI(self):

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu('&File')
        help_menu = menu_bar.addMenu('&Help')

        # open menu item
        open_action = QAction('&Open...', self)
        open_action.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        open_action.triggered.connect(self.open_dir)
        open_action.setStatusTip('Open directory')
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)

        # save menu item
        save_action = QAction('&Save', self)
        save_action.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        save_action.setStatusTip('Save the document')
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_map)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # exit menu item
        exit_action = QAction('&Exit', self)
        exit_action.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
        exit_action.setStatusTip('Exit')
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.quit)
        file_menu.addAction(exit_action)

        about_action = QAction('About', self)
        about_action.setIcon(self.style().standardIcon(QStyle.SP_DialogHelpButton))
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)
        about_action.setStatusTip('About')
        about_action.setShortcut('F1')

        # toolbar
        toolbar = QToolBar('Main ToolBar')
        self.addToolBar(toolbar)
        toolbar.setIconSize(QSize(16, 16))

        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addSeparator()

        toolbar.addAction(exit_action)

        # status bar
        self.status_bar = self.statusBar()

        self.count_label = QLabel("")
        self.statusBar().addPermanentWidget(self.count_label)

        # display the a message in 5 seconds
        self.status_bar.showMessage('Ready', 5000)


    def process_event(self, event_name, node, point, map):

        self.status_bar.showMessage(f"{event_name}: {node.name}")
        self.square_map.setToolTip(self.square_map.adapter.label(node))


    def about(self):

        QMessageBox.about(
            self,
            "About",
            "QSquareMap widget demo",
        )


    def confirm_save(self):

        message = f"Do you want to save changes to {self.path if self.path else 'Untitled'}?"
        MsgBoxBtn = QMessageBox.StandardButton
        MsgBoxBtn = MsgBoxBtn.Save | MsgBoxBtn.Discard | MsgBoxBtn.Cancel

        button = QMessageBox.question(
            self, QApplication.applicationName(), message, buttons=MsgBoxBtn
        )

        if button == MsgBoxBtn.Cancel:
            return False

        if button == MsgBoxBtn.Save:
            self.save_map()

        return True

    def write_file(self):

        self.path.write_text(self.text_edit.toPlainText())
        self.statusBar().showMessage('The file has been saved...', 3000)


    def save_map(self):
        # save the currently openned file
        if (self.path):
            return self.write_file()

        # save a new file
        filename, filetype = QFileDialog.getSaveFileName(
            self, 'Save File', filter=self.filters
        )

        if not filename:
            return

        self.path = Path(filename)
        self.write_file()
        self.set_title(filename)


    def open_dir(self):

        dir_name = QFileDialog.getExistingDirectory(self, "Open Directory", ".")
        if dir_name:
            self.setWindowTitle(dir_name)
            self.load_model(dir_name)


    def load_model(self, path):

        self.status_bar.showMessage(f"Load {path} ...")
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor));
        self.count = 0
        self.square_map.SetModel(self._load_model(path))
        self.count_label.setText(f"Count: {self.count}")
        QApplication.restoreOverrideCursor()


    def _load_model(self, path):
        nodes = []
        for name in sorted(Path(path).glob("*")):
            if name.is_symlink():
                continue
            if name.is_file():
                nodes.append(Node(name, name.stat().st_size, ()))
                self.count += 1
            elif name.is_dir() and name.name[0] != '.':
                nodes.append(self._load_model(name))
        return Node(path, sum([x.value for x in nodes]), nodes)


    def quit(self):
        if self.confirm_save():
            self.destroy()


def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == '__main__':

    main()
