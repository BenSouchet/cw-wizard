# Cardmarket Wishlist Wizard 🧙🏼‍♂️🪄

**CW Wizard** (Cardmarket Wishlist Wizard), is a *Python 3* script to find **the best deals** (bundles) that can be done for the cards you are looking for in your wishlists.

- Easily find the sellers with the most cards you are looking for 🃏
- Open Source script with MIT license, you can create you own Wizard 💫
- Fully commented, you can check what is done and how it's done 🧐
- Work with all card games available on Cardmarket (Magic: The Gathering, Yu-Gi-Oh!, Pokémon, ...) ✨

## How to Use
First, make sure that the [required packages are installed and up-to-date](https://github.com/BenSouchet/cw-wizard/blob/main/REQUIREMENTS.md#requirements)

Let’s get started by downloading the project:
```shell
> git clone https://github.com/BenSouchet/cw-wizard.git
Cloning into 'cw-wizard'...

> cd cw-wizard
```

Now you have two options: **scipt with a GUI** *(like a true software)* or **via command line** *(like a true developer)*

### Starting the Script with User Interface
1. In this case you need to make sure that **tkinter** is available on your computer ([check here](https://github.com/BenSouchet/cw-wizard/blob/main/REQUIREMENTS.md#optional)).
2. execute this command in your terminal:
```shell
> python3 cw-wizard-gui.py
```
3. Then simply follow the steps in the interface that popped up.

### Starting the Command Line Script
1. You need to first create a new JSON file at the root of the project directory named `credentials.json`
2. In that file, put your cardmarket credentials like in this example:
```json
{
    "login": "YOUR-USERNAME",
    "password": "YOUR-PASSWORD"
}
```
For info on why credentials are required [read this section](https://github.com/BenSouchet/cw-wizard/edit/main/README.md#security-and-authentification).

2. Check the script help (to see available parameters):
```shell
> python3 cw-wizard.py 
Hi there! I'm the Wizard, that do you want to do:
```

As you can see, you can call the script with one or more wishlist urls, and there is optional arguments available like `--max_sellers` ([info on script arguments](https://github.com/BenSouchet/cw-wizard/blob/main/README.md#script-arguments)).

3. A classic example would be:
```shell
> python3 cw-wizard.py -w https://www.cardmarket.com/en/Pokemon/Wants/10876807 -m 10
```
Another example with multiple wishlists:
```shell
> python3 cw-wizard.py -w https://www.cardmarket.com/en/Pokemon/Wants/10876807 https://www.cardmarket.com/en/Pokemon/Wants/10841970
```

### Script Arguments
With the command line version of the script you can use the following arguments:

| Argument Name | Description | Required |
|:-------------:|:-----------:|:--------:|
| `-h` *OR* `--help` | Display the help in your terminal | No |
| `-w` *OR* `--wishlist_urls` | One or more Cardmarket wishlists (wantlists) urls.<br />If you add multiple urls simply put a space between then (not a comma). | **Yes** |
| `-m` *OR* `--max_sellers` | The maximum number of sellers to display on the result page.<br />Default value `20`. `0` means display all. | No |
| `-se` *OR* `--stop_or_error` | Whatever to stop on non fatal requests errors.<br />Default value `True`. | No |


## Security and Authentification
Since Cardmarket Wantlists (wishlists) cannot be public this is required that you are logged in, so cards data can be retrieved.

This is why you credentials are required in order that the script work, if you aren't confident putting you credentials please review the code, since all the code is hosted here on Github you can see and check that nothing weird is done with your credentials.

## Origin of the Project
This project has been created because the exiting tools (provided by [Cardmarket](https://www.cardmarket.com/en/Pokemon/Wants/ShoppingWizard)) are good but somehow limited, with this open-souce script it's easy to get exactly the result wanted.  
If in the future, this project inspire others to create there own tools this would be a big success.

## Others Ressouces & Useful links
- [CardmarketToCSV](https://github.com/decdod/CardmarketToCSV) by [ddkod](https://github.com/decdod)
- [Python Requests Documentation](https://docs.python-requests.org/en/latest/user/quickstart/)

## Author & maintainer
CW Wizard has been created and is currently maintained by [Ben Souchet](https://github.com/BenSouchet).

The code present in this repository is under [MIT license](https://github.com/BenSouchet/sorbus/blob/main/LICENSE).
