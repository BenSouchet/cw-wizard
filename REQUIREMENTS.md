## Requirements
- **Python 3**
- **Requests**, elegant and simple HTTP library for Python.
To ensure **Requests** is installed in your computer, simply run this simple command in your terminal of choice:
```bash
python3 -m pip install requests
```
- **Beautiful Soup 4**, Python library for pulling data out of HTML and XML files.
Install it with this command in your terminal of choice:
```bash
python3 -m pip install beautifulsoup4
```
- **Browser Cookie 3**, Python package used to L\loads cookies used by your web browser into a cookiejar object. Required since Cardmarket is now protected by Cloudflare.
```bash
python3 -m pip install browser-cookie3
```

## Optional (needed for the User Interface script)
- **tkinter**, GUI framework for Python. Only needed if you want to use the GUI script (`cw-wizard-gui.py`).
 - For *Mac OS* users:
```bash
brew install python-tk
```
 - For *Ubuntu* & *Debian OS* users:
```bash
sudo apt-get install python3-tk
```
 - For *Windows* users, first check if the script work, if not then:  
You need to re-start (maybe re-download) the Python3 installer and **check** ☑️ the Optional Features named `tcl/tk and IDLE`.

![tck_tl_option](https://user-images.githubusercontent.com/17025808/153940505-4f0574b4-582d-470a-8731-fe04b5a7743d.png)
