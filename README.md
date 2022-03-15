# Cardmarket Wishlist Wizard 🧙🏼‍♂️🪄

![banner](https://user-images.githubusercontent.com/17025808/154534238-e8386e2f-c888-4f03-9855-c591dd19e85c.jpg)


**CW Wizard** (Cardmarket Wishlist Wizard), is a *Python 3* script to find **the best deals** (bundles) that can be done for the cards you are looking for in your wishlists.

- Easily find the sellers with the most cards you are looking for 🃏
- Open Source script with MIT license, you can create you own Wizard 💫
- Fully commented, you can check what is done and how it's done 🧐
- Work with all card games available on Cardmarket (Magic: The Gathering, Yu-Gi-Oh!, Pokémon, ...) ✨

**Disclaimer**: If you have activated the [Two-factor authentication (2FA)](https://en.wikipedia.org/wiki/Help:Two-factor_authentication) on your Cardmarket account this script won't work (this feature is not planned to be added soon).

## How to Use
It's a Python script, so first, make sure that the [required packages are installed and up-to-date](https://github.com/BenSouchet/cw-wizard/blob/main/REQUIREMENTS.md#requirements)

Let’s get started by downloading the project:
```shell
> git clone https://github.com/BenSouchet/cw-wizard.git
Cloning into 'cw-wizard'...

> cd cw-wizard
```

Now you have two options: ~~**scipt with a GUI** *(like a true software)* or~~ **via command line** *(like a true developer)*

### Starting the Script with a User Interface (Not Yet Available)
**/!\ Currently this option isn't available, use the script in command line. /!\\**
1. In this case you need to make sure that **tkinter** is available on your computer ([check here](https://github.com/BenSouchet/cw-wizard/blob/main/REQUIREMENTS.md#optional-needed-for-the-user-interface-script)).
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

**Bonus**: You can also directly start the script and create the `credentials.json` file interactively with the script.

3. Check the script help (to see available parameters):
```shell
> python3 cw-wizard.py -h
```
```text
usage: CW Wizard [-h] [-v] -w WISHLIST_URLS [WISHLIST_URLS ...] [-m MAX_SELLERS] [-c]

CW Wizard, Find the best bundles for the cards in your wishlist(s).

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -w WISHLIST_URLS [WISHLIST_URLS ...], --wishlist-urls WISHLIST_URLS [WISHLIST_URLS ...]
                        wishlist url(s) (if you pass multiples whislists, separate them with spaces)
  -m MAX_SELLERS, --max-sellers MAX_SELLERS
                        maximum number of sellers to display on the result page
  -c, --continue-on-error
                        if specified the script will continue on non fatal errors
```

As you can see, you can call the script with one or more wishlist urls, and there is optional arguments available ([info on script arguments](https://github.com/BenSouchet/cw-wizard/blob/main/README.md#script-arguments)).

4. A basic example would be:
```shell
> python3 cw-wizard.py -w https://www.cardmarket.com/en/Pokemon/Wants/10876807 -m 10
```
Example with multiple wishlists:
```shell
> python3 cw-wizard.py -w https://www.cardmarket.com/en/Pokemon/Wants/10876807 https://www.cardmarket.com/en/Pokemon/Wants/10841970
```
5. If everything goes well a result HTML page will open on your default web browser, otherwise check the terminal to see the error message(s).

### Script Arguments
With the command line version of the script you can use the following arguments:

| Argument Name | Description | Required |
|:-------------:|:-----------:|:--------:|
| `-v` *OR* `--version` | Display the version number of the script in your terminal | No |
| `-h` *OR* `--help` | Display the help in your terminal | No |
| `-w` *OR* `--wishlist_urls` | One or more Cardmarket wishlists (wantlists) urls.<br />If you add multiple urls simply put a space between then (not a comma). | **Yes** |
| `-m` *OR* `--max_sellers` | The maximum number of sellers to display on the result page.<br />Default value `20`. `0` means display all. | No |
| `-c` *OR* `--continue_on_error` | Whatever to stop on non fatal requests errors.<br />Default value `False`. | No |

## Sorting Relevant Sellers
Currently the most relevant sellers are the ones with the most cards you are looking for in your wishlists.  
A more accurate way for sorting the sellers would be with cards prices and cards rarity:
 1. **Rarity Index** : Every rarity get a value from 1 to N (stating from the rarest to the more common).  
We can assign the same rarity index for multiple rarities if they are equally "rare" ("rare" can be discribe as the percentage of chance to get this card in a booster).
 3. **Card Index** : For every cards in a seller list we multiply the card rarity by the price.
 4. **Total** : Sum the cards Indexes and divide by the number of cards to get an average.
 5. **Normalizing** : when every sellers is done, the seller with the highest total value represent a deal index of 50% and the seller with the lower total value represent 100%. For all the other sellers do cross product to determine the deal index according to the highest and lowest we just find.

**BUT** the technic describe above is very good *"in theory"* but some **heavy** limitations occur:
- First point, there is **A LOT** of card rarities, across the different TCGs. Since we need to assign value (rarity index) for all of them this can get pretty messy.
- Second and most important point, cards with the same rarity aren't equally "rare", for example **Charizard 4/102** and **Alakazam 1/102** are both *holofoil rare* but **Charizard** is way more "rare" because of popularity. So, in the equation a **Popularity Index** need to be added for every cards...

As you can understand implementing a more accurate sorting system is not an easy task at all, and require lot of data.  
If you have another method in mind let me know 🙂

## Security and Authentification
Since Cardmarket Wantlists (wishlists) cannot be public this is required that you are logged in, so cards data can be retrieved.

This is why you credentials are required in order that the script work, if you aren't confident putting you credentials please review the code, since all the code is hosted here on Github you can see and check that nothing weird is done with your credentials.

As indicated at the beginning of this README, accounts with [Two-factor authentication (2FA)](https://en.wikipedia.org/wiki/Help:Two-factor_authentication) enabled won't be able to use this script, currently the feature is not planned to be added to the project.

## Origin of the Project
This project has been created because the exiting tools (provided by [Cardmarket](https://www.cardmarket.com/en/Pokemon/Wants/ShoppingWizard)) are good but somehow limited, with this open-souce script it's easy to get exactly the result wanted.  
If in the future, this project inspire others to create there own tools this would be a big success.

## Others Ressouces & Useful links
- [CardmarketToCSV](https://github.com/decdod/CardmarketToCSV) by [ddkod](https://github.com/decdod)
- [Python Requests Documentation](https://docs.python-requests.org/en/latest/user/quickstart/)
- [Tillana Font](https://fonts.google.com/specimen/Tillana) by the [Indian Type Foundry](https://www.indiantypefoundry.com/) (License: [Open Font License](https://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL))

## Author & maintainer
CW Wizard has been created and is currently maintained by [Ben Souchet](https://github.com/BenSouchet).

The code present in this repository is under [MIT license](https://github.com/BenSouchet/cw-wizard/blob/main/LICENSE).
