# RDP Server Monitor

![RDP Server Monitor Logo](/icons/logo.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-green)](https://pypi.org/project/PyQt5/)

A powerful and user-friendly application for monitoring Remote Desktop Protocol (RDP) servers with real-time updates and customizable alerts.


## 🌟 Features

- 🖥️ Monitor multiple RDP servers simultaneously
- 👥 Display connected users for each server
- 🔍 Monitor and display status of specified processes and services
- 🔄 Real-time updates with configurable refresh intervals
- ➕ Add, remove, and configure servers dynamically
- 🚨 Customizable IT user detection and alerts
- 🌐 Multi-language support (English and Portuguese)
- 🎨 Themeable interface (Light, Dark, and Blue themes)
- 📱 Responsive layout adapting to window size

## 🚀 Getting Started

### Prerequisites

- Python 3.6 or higher
- PyQt5 5.15 or higher


## 🐱‍🏍 First time run
- Upon opening the app for the first time, you'll have to add your servers and configure the IT users manually.
#
## 📸 Screenshots

<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/88e1f2c5-d251-418a-b3ac-7776b0f4e4af" alt="Light Theme" width="400"/></td>
    <td><img src="https://github.com/user-attachments/assets/9e24a05e-614d-4d45-aa6c-2bc2301bcd24" alt="Dark Theme" width="400"/></td>
  </tr>
  <tr>
    <td>Light Theme</td>
    <td>Dark Theme</td>
  </tr>
  <tr><td><img src="https://github.com/user-attachments/assets/92f7f107-f789-4abf-9222-feda0f630536" alt="Example" width="400"/></td>
  </tr>
  <tr>
    <td>Server Example</td>
  </tr>
</table>

## 🛠️ Configuration

The application uses a `server_config.json` file to store server information and settings. You can edit this file directly or use the in-app interface to add and remove servers.

![image](https://github.com/user-attachments/assets/529b4897-43d9-4e8e-8594-6137e6c0e93c)


Example configuration:

```json
{
  "servers": [
    {
      "name": "Server 1",
      "ip": "192.168.1.100",
      "processes": ["process1.exe", "process2.exe"],
      "services": ["service1", "service2"]
    }
  ],
  "ti_users": ["admin", "it_support"]
}
```


## 🌍 Internationalization

The application supports both English and Portuguese languages. You can select your preferred language when starting the application.

To add more languages:

1. Update the `translations.py` file with new language entries.
2. Add translated strings for all existing entries.


## 🎨 Themes

RDP Server Monitor offers three built-in themes:

- Light
- Dark
- Blue
