import sys,subprocess
from PySide6.QtWidgets import QApplication,QMainWindow, QWidget, QVBoxLayout,QHBoxLayout, QLabel, QPushButton,QListView
from PySide6.QtCore import Qt,QTimer, QStringListModel
import getIPs

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Gamepad Viewer")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.mlayout = QVBoxLayout()
        toplayout = QHBoxLayout()
        self.label = QLabel("Select up to 2 cameras to stream")
        self.refbutton = QPushButton("\u21BB")
        self.refbutton.clicked.connect(self.ref_clicked)
        toplayout.addWidget(self.label,1)
        toplayout.addWidget(self.refbutton,0)
        self.listbox = QListView()
        self.listbox.setSelectionMode(QListView.MultiSelection)
        self.model = QStringListModel()
        self.listbox.setModel(self.model)
        buttonlayout = QHBoxLayout()
        self.qtbutton = QPushButton("QT Viewer")
        self.qtbutton.clicked.connect(self.open_qt_viewer)
        self.glbutton = QPushButton("GL Viewer")
        self.glbutton.clicked.connect(self.open_gl_viewer)
        buttonlayout.addWidget(self.qtbutton)
        buttonlayout.addWidget(self.glbutton)

        self.mlayout.addLayout(toplayout)
        self.mlayout.addWidget(self.listbox)
        self.mlayout.addLayout(buttonlayout)
        self.central_widget.setLayout(self.mlayout)

    def ref_clicked(self):
        ips = getIPs.getIPs()
        if ips:
            self.model.setStringList(ips)

    def open_qt_viewer(self):
        import qtcontroller
        selected_indexes = self.listbox.selectedIndexes()
        selected_items = [self.model.data(index, Qt.DisplayRole) for index in selected_indexes]
        if selected_items:
            qtc = qtcontroller.QtController(selected_items[0],self)
            qtc.setParent(self)
            qtc.show()

    def open_gl_viewer(self):
        import vrcontroller
        selected_indexes = self.listbox.selectedIndexes()
        selected_items = [self.model.data(index, Qt.DisplayRole) for index in selected_indexes]
        if selected_items:
            python_interpreter = sys.executable
            command = [python_interpreter, "vrcontroller.py"] + selected_items
            process = subprocess.Popen(command)


    def update_gamepad_status(self):
        inputs = self.gamepad_handler.get_input()
        status_text = "Gamepad Input:\n"
        for i, (axes, buttons) in enumerate(inputs):
            status_text += f"Gamepad {i}:\n"
            status_text += f"  Axes: {axes}\n"
            status_text += f"  Buttons: {buttons}\n"
        self.label.setText(status_text)
    
    def showEvent(self,event):
        ips = getIPs.getIPs()
        if ips:
            self.model.setStringList(ips)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())
