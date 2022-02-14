# Cardmarket Wishlist Wizard 🧙🏼‍♂️🪄

**CW Wizard** (Cardmarket Wishlist Wizard), is a Python 3 script to find the best deals (bundles) that can be done for the cards you are looking for in your wishlists.

- Easily find the sellers with the most cards you are looking for 🃏
- Open Source script with MIT license, you can create you own Wizard 💫
- Fully commented, you can check what is done and how it's done 🧐
- Work with all Card Games available on Cardmarket (Magic: The Gathering, Yu-Gi-Oh!, Pokémon, ...)

## How to Use
First, make sure that the [required packages are installed and up-to-date]()

Let’s get started by downloading the project:
```shell
> git clone https://github.com/BenSouchet/cw-wizard.git
Cloning into 'cw-wizard'...

> cd cw-wizard
```

Now you have two options: **scipt with a GUI** *(like a true software)* or **via command line** *(like a true developer)*

### Starting the script with a GUI
1. In this case you need to make sure that **tkinter** is available on your computer ([check here]()).
2. execute this command in your terminal:
```shell
> python3 cw-wizard-gui.py
```
3. Then simply follow the steps in the interface that popped up.

### Starting the command line script
1. You need to first create a new JSON file at the root of the project directory named `credentials.json`
2. In that file, put your cardmarket credentials like in this example:
```json
{
    "login": "YOUR-USERNAME",
    "password": "YOUR-PASSWORD"
}
```
For info on why credentials are required [read this section]().

2. Check the script help (to see available parameters):
```shell
> python3 cw-wizard.py 
Hi there! I'm the Wizard, that do you want to do:
```

As you can see you can call the script with one or more wishlist urls and some optional parameters.

3. A basic example would be:
```shell
> python3 cw-wizard.py -w https://www.cardmarket.com/en/Pokemon/Wants/10876807 -m 10
```

## Security and Authentification
Since Cardmarket Wantlists (wishlists) cannot be public this is required that you are logged in.

This is why you credentials are required in order that the script work, if you aren't confident putting you credentials please review the code, since all the code is hosted here on Github you can see and check that nothing weird is done with your credentials.

## Script Parameters


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

## Optional
- **tkinter**, GUI framework for Python. Only needed if you want to use `wizard_gui.py`.
 - For Mac OS users:
```bash
brew install python-tk
```
 - For Ubuntu & Debian OS users:
```bash
sudo apt-get install python3-tk
```
 - For Windows users (tkinter fail):  
You need to re-start (maybe re-download) the Python3 installer and **check** ☑️ the Optional Features named `tcl/tk and IDLE`.


