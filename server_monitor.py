import sys
import subprocess
import os
import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QComboBox, QScrollArea, QFormLayout,
                             QGridLayout, QFrame, QListWidget, QSizePolicy, QDialog, QDialogButtonBox,
                             QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from translations import Translator


# Global translator
translator = Translator('en')  # Default to English


# Helper function to translate text
def _(text):
    return translator.translate(text)


def resource_path(relative_path):
    """ Get absolute path to resource, works for PyInstaller bundles """
    try:
        # PyInstaller stores temp files in _MEIPASS when bundled
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Use resource_path to get the correct path for your icons folder
ICON_PATH = resource_path("icons/")
CONFIG_FILE = "server_config.json"


class ServerMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RDP Server Monitor")
        self.setGeometry(100, 100, 1200, 800)
        # Set the application icon for taskbar and window
        self.setWindowIcon(QIcon(resource_path('favicon.ico')))
        self.bg_color = "#013861"
        self.button_color = "#0098D7"

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)  # Add some padding
        self.setup_header()
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(1)  # Reduce spacing between server widgets
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrollbar
        self.layout.addWidget(self.scroll_area)

        self.setup_theme_selector()
        self.setup_search_bar()

        self.load_config()

        # Initialize the server_widgets dictionary
        self.server_widgets = {}

        self.setup_server_widgets()

        self.apply_theme("light")

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_all_servers)
        self.refresh_timer.start(60000)  # Refresh every 1 minute

        self.last_refresh = datetime.now()
        self.update_refresh_indicator()

        # Add a timer to check for window size changes
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_layout)
        self.last_width = self.width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.setup_server_widgets)  # Redraw widgets after resize

    def update_layout(self):
        self.last_width = self.width()
        self.setup_server_widgets()

    def setup_server_widgets(self):
        # Clear existing widgets
        for widget in self.server_widgets.values():
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()
        self.server_widgets.clear()

        window_width = self.scroll_area.viewport().width()
        num_columns = min(3, max(1, window_width // 350))  # Limit to 3 columns maximum

        for idx, (name, ip, processes, services) in enumerate(self.servers):
            server_widget = ServerWidget(name, ip, self.ti_users, processes, services, self)
            self.server_widgets[name] = server_widget
            row = idx // num_columns
            col = idx % num_columns
            self.scroll_layout.addWidget(server_widget, row, col)

        # Set the minimum width of the scroll widget to ensure proper layout
        min_width = num_columns * 350 + (num_columns - 1) * self.scroll_layout.spacing()
        self.scroll_widget.setMinimumWidth(min_width)

        # Ensure all columns have equal stretch
        for col in range(num_columns):
            self.scroll_layout.setColumnStretch(col, 1)

        # Update the scroll area
        self.scroll_widget.updateGeometry()
        self.scroll_area.updateGeometry()

    def setup_search_bar(self):
        search_layout = QHBoxLayout()
        search_label = QLabel(_("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(_("Type to search servers..."))
        self.search_input.textChanged.connect(self.filter_servers)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)

    def filter_servers(self):
        search_text = self.search_input.text().lower()
        for name, server_widget in self.server_widgets.items():
            if search_text in name.lower():
                server_widget.show()
            else:
                server_widget.hide()

    def setup_header(self):
        header_layout = QHBoxLayout()

        logo_label = QLabel()
        logo_pixmap = QPixmap(f"{ICON_PATH}logo.png").scaled(170, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)

        header_layout.addStretch()

        self.refresh_indicator = QLabel()
        header_layout.addWidget(self.refresh_indicator)

        refresh_all_button = QPushButton(_("Refresh All"))
        refresh_all_button.clicked.connect(self.refresh_all_servers)
        header_layout.addWidget(refresh_all_button)

        configure_ti_button = QPushButton(_("Configure IT"))
        configure_ti_button.clicked.connect(self.open_ti_config)
        header_layout.addWidget(configure_ti_button)

        add_server_button = QPushButton(_("Add Server"))
        add_server_button.clicked.connect(self.open_add_server_dialog)
        header_layout.addWidget(add_server_button)

        self.layout.addLayout(header_layout)

    def setup_theme_selector(self):
        theme_layout = QHBoxLayout()
        theme_label = QLabel(_("Theme:"))
        self.theme_selector = QComboBox()
        self.theme_selector.addItems([_("Light"), _("Dark"), _("Blue")])
        self.theme_selector.setCurrentText(_("Light"))
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_selector)
        theme_layout.addStretch()
        self.layout.addLayout(theme_layout)


    def refresh_all_servers(self):
        for server_widget in self.server_widgets.values():
            server_widget.refresh_users()
        self.last_refresh = datetime.now()
        self.update_refresh_indicator()

    def update_refresh_indicator(self):
        next_refresh = self.last_refresh + timedelta(minutes=1)
        self.refresh_indicator.setText(
            f"Last Update: {self.last_refresh.strftime('%H:%M:%S')} | Next: {next_refresh.strftime('%H:%M:%S')}")

    def open_ti_config(self):
        dialog = TIConfigDialog(self.ti_users, self)
        if dialog.exec_():
            self.ti_users = dialog.get_ti_users()
            self.save_config()
            for server_widget in self.server_widgets.values():
                server_widget.update_ti_users(self.ti_users)

    def open_add_server_dialog(self):
        dialog = AddServerDialog(self)
        if dialog.exec_():
            name, ip = dialog.get_server_info()
            self.add_server(name, ip)

    def add_server(self, name, ip):
        self.servers.append((name, ip, [], []))  # Add empty lists for processes and services
        server_widget = ServerWidget(name, ip, self.ti_users, [], [], self)
        self.server_widgets[name] = server_widget
        self.save_config()
        self.setup_server_widgets()


    def remove_server(self, name):
        if name in self.server_widgets:
            server_widget = self.server_widgets.pop(name)
            server_widget.deleteLater()
            self.servers = [server for server in self.servers if server[0] != name]
            self.save_config()
            self.setup_server_widgets()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            self.servers = []
            for server in config.get('servers', []):
                if isinstance(server, dict):
                    self.servers.append((
                        server['name'],
                        server['ip'],
                        server.get('processes', []),
                        server.get('services', [])
                    ))
                else:
                    # Unexpected format, skip this server
                    continue
            self.ti_users = config.get('ti_users', [])
        except FileNotFoundError:
            self.servers = [
                ("Default Gateway", "192.6.1.1", [], [])
            ]
            self.ti_users = []

    def save_config(self):
        config = {
            'servers': [{'name': name, 'ip': ip, 'processes': processes, 'services': services} for
                        name, ip, processes, services in self.servers],
            'ti_users': self.ti_users
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

    def change_theme(self, theme):
        theme_map = {
            "Light": "light", "Claro": "light",
            "Dark": "dark", "Escuro": "dark",
            "Blue": "blue", "Azul": "blue"
        }
        self.apply_theme(theme_map[theme])

    def apply_theme(self, theme):
        if theme == "light":
            self.setStyleSheet(f"""
                QMainWindow, QScrollArea, QWidget#scroll_widget {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                        stop: 0 {self.bg_color}, 
                        stop: 1 #0098D7);
                }}
                QLabel, QPushButton, QLineEdit, QComboBox, QListWidget {{
                    color: black;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }}
                QFrame {{
                    background-color: white;
                    border: 1px solid #dddddd;
                    border-radius: 8px;
                }}
                QPushButton {{
                    background-color: {self.button_color};
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: #0056b3;
                }}
                QListWidget {{
                    border: 1px solid #dddddd;
                    border-radius: 4px;
                    background-color: white;
                }}
            """)
        elif theme == "dark":
            self.setStyleSheet(f"""
            QMainWindow, QScrollArea, QWidget#scroll_widget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                    stop: 0 #1a1a1a, 
                    stop: 1 #2c2c2c);
            }}
            QLabel, QLineEdit, QComboBox, QListWidget {{
                color: darkgray;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QFrame {{
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }}
            QPushButton {{
                background-color: #5e5e5e;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #0077cc;
            }}
            QListWidget {{
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                background-color: #2a2a2a;
            }}
            QComboBox {{
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 2px 8px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #3a3a3a;
                border-left-style: solid;
            }}
            QComboBox::down-arrow {{
                image: url({ICON_PATH}dropdown_arrow_dark.svg);
            }}
            QScrollBar:vertical {{
                border: none;
                background: #2a2a2a;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #4a4a4a;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: #2a2a2a;
                height: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: #4a4a4a;
                min-width: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)
        elif theme == "blue":
            self.setStyleSheet(f"""
                QMainWindow, QScrollArea, QWidget#scroll_widget {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                        stop: 0 #001F3F, 
                        stop: 1 #0074D9);
                }}
                QLabel, QPushButton, QLineEdit, QComboBox, QListWidget {{
                    color: darkgray;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }}
                QFrame {{
                    background-color: #003366;
                    border: 1px solid #0056b3;
                    border-radius: 8px;
                }}
                QPushButton {{
                    background-color: #0098D7;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: #00b8ff;
                }}
                QListWidget {{
                    border: 1px solid #0056b3;
                    border-radius: 4px;
                    background-color: #004080;
                }}
            """)
        self.scroll_widget.setObjectName("scroll_widget")


class ServerWidget(QFrame):
    def __init__(self, name, ip, ti_users, processes, services, parent):
        super().__init__()
        self.name = name
        self.ip = ip
        self.ti_users = ti_users
        self.processes = processes
        self.services = services
        self.parent = parent
        self.layout = QVBoxLayout(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        header_layout = QHBoxLayout()
        server_icon = QLabel()
        server_icon.setPixmap(QIcon(f"{ICON_PATH}server.svg").pixmap(QSize(24, 24)))
        self.name_label = QLabel(f"<b>{name}</b>")
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet("background-color: gray; border-radius: 8px;")
        header_layout.addWidget(server_icon)
        header_layout.addWidget(self.name_label)
        header_layout.addWidget(self.status_indicator)
        header_layout.addStretch()

        self.layout.addLayout(header_layout)

        ip_layout = QHBoxLayout()
        ip_icon = QLabel()
        ip_icon.setPixmap(QIcon(f"{ICON_PATH}ip.svg").pixmap(QSize(24, 24)))
        self.ip_label = QLabel(f"IP: {ip}")
        ip_layout.addWidget(ip_icon)
        ip_layout.addWidget(self.ip_label)
        ip_layout.addStretch()
        self.layout.addLayout(ip_layout)

        users_layout = QHBoxLayout()
        users_icon = QLabel()
        users_icon.setPixmap(QIcon(f"{ICON_PATH}users.svg").pixmap(QSize(24, 24)))
        users_label = QLabel(_("Connected IT:"))
        users_layout.addWidget(users_icon)
        users_layout.addWidget(users_label)
        users_layout.addStretch()
        self.layout.addLayout(users_layout)

        self.users_list = QListWidget()
        self.users_list.setMaximumHeight(100)
        self.layout.addWidget(self.users_list)

        self.ti_warning_widget = QWidget()
        self.ti_warning_layout = QHBoxLayout(self.ti_warning_widget)
        self.ti_warning_layout.setContentsMargins(0, 0, 0, 0)
        self.ti_warning_layout.setSpacing(5)  # Reduce spacing between icon and text

        self.ti_icon_label = QLabel()
        self.ti_warning_label = QLabel()
        self.ti_warning_label.setWordWrap(True)  # Allow text wrapping

        self.ti_warning_layout.addWidget(self.ti_icon_label)
        self.ti_warning_layout.addWidget(self.ti_warning_label, 1)  # Give the label more space
        self.ti_warning_layout.addStretch()  # Push everything to the left

        self.layout.addWidget(self.ti_warning_widget)
        self.ti_warning_widget.hide()

        processes_layout = QHBoxLayout()
        processes_icon = QLabel()
        processes_icon.setPixmap(QIcon(f"{ICON_PATH}services.svg").pixmap(QSize(24, 24)))
        processes_label = QLabel(_("Monitored Processes:"))
        processes_layout.addWidget(processes_icon)
        processes_layout.addWidget(processes_label)
        processes_layout.addStretch()
        self.layout.addLayout(processes_layout)

        self.processes_list = QListWidget()
        self.processes_list.setMaximumHeight(100)
        self.layout.addWidget(self.processes_list)
        self.update_processes_list()

        services_layout = QHBoxLayout()
        services_icon = QLabel()
        services_icon.setPixmap(QIcon(f"{ICON_PATH}services.svg").pixmap(QSize(24, 24)))
        services_label = QLabel(_("Monitored Services:"))
        services_layout.addWidget(services_icon)
        services_layout.addWidget(services_label)
        services_layout.addStretch()
        self.layout.addLayout(services_layout)

        self.services_list = QListWidget()
        self.services_list.setMaximumHeight(100)
        self.layout.addWidget(self.services_list)
        self.update_services_list()

        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton(_("Update"))
        self.refresh_button.setIcon(QIcon(f"{ICON_PATH}refresh.svg"))
        self.refresh_button.clicked.connect(self.refresh_users)
        button_layout.addWidget(self.refresh_button)

        self.delete_button = QPushButton(_("Delete"))
        self.delete_button.setIcon(QIcon(f"{ICON_PATH}delete.svg"))
        self.delete_button.clicked.connect(self.delete_server)
        button_layout.addWidget(self.delete_button)

        self.monitor_processes_button = QPushButton(_("Processes"))
        self.monitor_processes_button.setIcon(QIcon(f"{ICON_PATH}monitor.svg"))
        self.monitor_processes_button.clicked.connect(self.open_monitor_processes_dialog)
        button_layout.addWidget(self.monitor_processes_button)

        self.monitor_services_button = QPushButton(_("Services"))
        self.monitor_services_button.setIcon(QIcon(f"{ICON_PATH}monitor.svg"))
        self.monitor_services_button.clicked.connect(self.open_monitor_services_dialog)
        button_layout.addWidget(self.monitor_services_button)

        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        self.setFrameShape(QFrame.StyledPanel)

        self.worker = QwinstaWorker(self.ip, self.processes, self.services)
        self.worker.finished.connect(self.update_users)
        self.worker.start()

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_indicator)
        self.blink_state = False
        self.blink_timer.setInterval(1000)  # Slower blink, every 1 second

    def refresh_users(self):
        self.users_list.clear()
        self.users_list.addItem("Loading...")
        self.worker.start()

    def update_users(self, users, running_processes, running_services):
        self.users_list.clear()
        for user in users:
            self.users_list.addItem(user)

        if users:
            self.status_indicator.setStyleSheet("background-color: #4CAF50; border-radius: 8px;")
            self.blink_timer.start()
        else:
            self.status_indicator.setStyleSheet("background-color: gray; border-radius: 8px;")
            self.blink_timer.stop()

        self.update_ti_warning(users)
        self.update_processes_status(running_processes)
        self.update_services_status(running_services)

    def open_monitor_processes_dialog(self):
        dialog = MonitorProcessesDialog(self.processes, self)
        if dialog.exec_():
            self.processes = dialog.get_processes()
            self.update_processes_list()
            self.worker.processes = self.processes
            self.parent.save_config()

    def open_monitor_services_dialog(self):
        dialog = MonitorServicesDialog(self.services, self)
        if dialog.exec_():
            self.services = dialog.get_services()
            self.update_services_list()
            self.worker.services = self.services
            self.parent.save_config()

    def update_processes_list(self):
        self.processes_list.clear()
        for process in self.processes:
            self.processes_list.addItem(process)

    def update_services_list(self):
        self.services_list.clear()
        for service in self.services:
            self.services_list.addItem(service)

    def update_processes_status(self, running_processes):
        for i in range(self.processes_list.count()):
            item = self.processes_list.item(i)
            process = item.text()
            if process in running_processes:
                item.setForeground(Qt.green)
            else:
                item.setForeground(Qt.red)

    def update_services_status(self, running_services):
        for i in range(self.services_list.count()):
            item = self.services_list.item(i)
            service = item.text()
            if service in running_services:
                item.setForeground(Qt.green)
            else:
                item.setForeground(Qt.red)

    def toggle_indicator(self):
        self.blink_state = not self.blink_state
        opacity = 1 if self.blink_state else 0.5
        self.status_indicator.setStyleSheet(f"background-color: rgba(76, 175, 80, {opacity}); border-radius: 8px;")

    def update_ti_users(self, ti_users):
        self.ti_users = ti_users
        self.update_ti_warning([self.users_list.item(i).text() for i in range(self.users_list.count())])

    def update_ti_warning(self, users):
        detected_ti = [user for user in users if user in self.ti_users]
        if detected_ti:
            icon_pixmap = QIcon(f"{ICON_PATH}it_icon.svg").pixmap(QSize(16, 16))
            self.ti_icon_label.setPixmap(icon_pixmap)
            self.ti_icon_label.setFixedSize(16, 16)  # Fix the size of the icon

            warning_text = f"{_('IT detected:')} {', '.join(detected_ti)}"
            self.ti_warning_label.setText(warning_text)

            self.ti_warning_widget.show()
        else:
            self.ti_warning_widget.hide()

    def delete_server(self):
        reply = QMessageBox.question(self, _('Confirm Deletion'),
                                     f"{_('Are you sure you want to delete the server')} '{self.name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.parent.remove_server(self.name)

    def open_monitor_services_dialog(self):
        dialog = MonitorServicesDialog(self.services, self)
        if dialog.exec_():
            self.services = dialog.get_services()
            self.update_services_list()
            self.worker.services = self.services
            self.parent.save_config()

    def update_services_list(self):
        self.services_list.clear()
        for service in self.services:
            self.services_list.addItem(service)

    def update_services_status(self, running_services):
        for i in range(self.services_list.count()):
            item = self.services_list.item(i)
            service = item.text()
            if service in running_services:
                item.setForeground(Qt.green)
            else:
                item.setForeground(Qt.red)


class QwinstaWorker(QThread):
    finished = pyqtSignal(list, list, list)

    def __init__(self, ip, processes, services):
        super().__init__()
        self.ip = ip
        self.processes = processes
        self.services = services

    def run(self):
        try:
            if self.ip == "10.12.82.2":  # Special handling for Windows Server 2012 R2
                result = subprocess.run(["qwinsta", "/server:" + self.ip], capture_output=True, text=True,
                                        encoding='utf-16-le', creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                result = subprocess.run(["qwinsta", "/server:" + self.ip], capture_output=True, text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW)

            if result.stdout:  # Check if there's any output
                users = [line.split()[1] for line in result.stdout.splitlines()[1:] if "rdp-tcp#" in line.lower()]
            else:
                users = ["No server response."]

            running_processes = self.check_processes()
            running_services = self.check_services()
            self.finished.emit(users, running_processes, running_services)

        except Exception as e:
            self.finished.emit([f"Error: {str(e)}"], [], [])

    def check_processes(self):
        running_processes = []
        for process in self.processes:
            try:
                result = subprocess.run(["tasklist", "/S", self.ip, "/NH", "/FI", f"IMAGENAME eq {process}"],
                                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if process.lower() in result.stdout.lower():
                    running_processes.append(process)
            except Exception:
                pass
        return running_processes

    def check_services(self):
        running_services = []
        for service in self.services:
            try:
                result = subprocess.run(["sc", "\\\\" + self.ip, "query", service], capture_output=True, text=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                if "RUNNING" in result.stdout:
                    running_services.append(service)
            except Exception:
                pass
        return running_services


class TIConfigDialog(QDialog):
    def __init__(self, ti_users, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Configure IT Users"))
        self.layout = QVBoxLayout(self)

        self.ti_users_list = QListWidget()
        self.ti_users_list.addItems(ti_users)
        self.layout.addWidget(self.ti_users_list)

        self.new_user_input = QLineEdit()
        self.layout.addWidget(self.new_user_input)

        add_button = QPushButton(_("Add User"))
        add_button.clicked.connect(self.add_user)
        self.layout.addWidget(add_button)

        remove_button = QPushButton(_("Remove Selected User"))
        remove_button.clicked.connect(self.remove_user)
        self.layout.addWidget(remove_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def add_user(self):
        user = self.new_user_input.text().strip()
        if user:
            self.ti_users_list.addItem(user)
            self.new_user_input.clear()

    def remove_user(self):
        current_item = self.ti_users_list.currentItem()
        if current_item:
            self.ti_users_list.takeItem(self.ti_users_list.row(current_item))

    def get_ti_users(self):
        return [self.ti_users_list.item(i).text() for i in range(self.ti_users_list.count())]


class AddServerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Add Server"))
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.ip_input = QLineEdit()

        self.layout.addRow(_("Server Name:"), self.name_input)
        self.layout.addRow(_("Server IP:"), self.ip_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def get_server_info(self):
        return self.name_input.text().strip(), self.ip_input.text().strip()


class MonitorProcessesDialog(QDialog):
    def __init__(self, processes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Monitor Processes"))
        self.layout = QVBoxLayout(self)

        self.processes_list = QListWidget()
        self.processes_list.addItems(processes)
        self.layout.addWidget(self.processes_list)

        self.new_process_input = QLineEdit()
        self.layout.addWidget(self.new_process_input)

        add_button = QPushButton(_("Add Process"))
        add_button.clicked.connect(self.add_process)
        self.layout.addWidget(add_button)

        remove_button = QPushButton(_("Remove Selected Process"))
        remove_button.clicked.connect(self.remove_process)
        self.layout.addWidget(remove_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def add_process(self):
        process = self.new_process_input.text().strip()
        if process:
            self.processes_list.addItem(process)
            self.new_process_input.clear()

    def remove_process(self):
        current_item = self.processes_list.currentItem()
        if current_item:
            self.processes_list.takeItem(self.processes_list.row(current_item))

    def get_processes(self):
        return [self.processes_list.item(i).text() for i in range(self.processes_list.count())]


class MonitorServicesDialog(QDialog):
    def __init__(self, services, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Monitor Services"))
        self.layout = QVBoxLayout(self)

        self.services_list = QListWidget()
        self.services_list.addItems(services)
        self.layout.addWidget(self.services_list)

        self.new_service_input = QLineEdit()
        self.layout.addWidget(self.new_service_input)

        add_button = QPushButton(_("Add Service"))
        add_button.clicked.connect(self.add_service)
        self.layout.addWidget(add_button)

        remove_button = QPushButton(_("Remove Selected Service"))
        remove_button.clicked.connect(self.remove_service)
        self.layout.addWidget(remove_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

    def add_service(self):
        service = self.new_service_input.text().strip()
        if service:
            self.services_list.addItem(service)
            self.new_service_input.clear()

    def remove_service(self):
        current_item = self.services_list.currentItem()
        if current_item:
            self.services_list.takeItem(self.services_list.row(current_item))

    def get_services(self):
        return [self.services_list.item(i).text() for i in range(self.services_list.count())]


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Add language selection
    language_dialog = QDialog()
    language_dialog.setWindowTitle(_("Select Language"))
    language_layout = QVBoxLayout(language_dialog)

    language_combo = QComboBox()
    language_combo.addItems(["English", "Português"])
    language_layout.addWidget(language_combo)

    ok_button = QPushButton(_("OK"))
    ok_button.clicked.connect(language_dialog.accept)
    language_layout.addWidget(ok_button)

    if language_dialog.exec_() == QDialog.Accepted:
        selected_language = 'en' if language_combo.currentText() == "English" else 'pt'
        translator.language = selected_language

    window = ServerMonitor()
    window.show()
    sys.exit(app.exec_())
