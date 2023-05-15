# Cardmarket Wantlist Wizard 🧙🏼‍♂️🪄

![banner](https://user-images.githubusercontent.com/17025808/154534238-e8386e2f-c888-4f03-9855-c591dd19e85c.jpg)


**CW Wizard** (Cardmarket Wantlist Wizard), is a *Python 3* script to find **the best deals** (bundles) that can be done for the cards you are looking for in your wantlists.

- **Bypass Cloudflare security** 🔓
- Easily find the sellers with the most cards you are looking for 🃏
- Open Source script with MIT license, you can create you own Wizard 💫
- Fully commented, you can check what is done and how it's done 🧐
- Work with all card games available on Cardmarket (Magic: The Gathering, Yu-Gi-Oh!, Pokémon, ...) ✨

![example_wizard](https://user-images.githubusercontent.com/17025808/159021646-7be4c2e8-4177-430c-97cd-e6d0f716501d.png)


**Disclaimer**: If you have activated the [Two-factor authentication (2FA)](https://en.wikipedia.org/wiki/Help:Two-factor_authentication) on your Cardmarket account this script won't work (this feature is **not** planned to be added soon).

## How to Use
It's a Python script, so first, make sure that the [required packages are installed and up-to-date](https://github.com/BenSouchet/cw-wizard/blob/main/REQUIREMENTS.md#requirements)

Let’s get started by downloading the project:
```shell
> git clone https://github.com/BenSouchet/cw-wizard.git
Cloning into 'cw-wizard'...

> cd cw-wizard
```

Now you have two options: the **script with a User Interface** *(like a true software)* or **via command line** *(like a true developer)*

### Starting the Script with a User Interface
1. In this case you need to make sure that **tkinter** is available on your computer ([check here](https://github.com/BenSouchet/cw-wizard/blob/main/REQUIREMENTS.md#optional-needed-for-the-user-interface-script)).
2. Open on your favorite browser one Cardmarket tab (just one).
3. Execute this command in your terminal:
```shell
> python3 cw-wizard-gui.py
```
4. Then simply follow the steps in the interface that popped up.

### Starting the Command Line Script
1. Open, on your favorite browser, one Cardmarket tab (just one)
2. Check the script help (to see available parameters):
```shell
> python3 cw-wizard.py -h
```
```text
usage: CW Wizard [-h] [-v] -b BROWSER_NAME -u WANTLIST_URLS [WANTLIST_URLS ...] [-m MAX_SELLERS] [-w] [-c]

CW Wizard v1.0.4, Find the best bundles for the cards in your wantlist(s).

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -b BROWSER_NAME, --browser_name BROWSER_NAME
                        Specify the browser name you used to open the Cardmarket tab (needed to bypass Cloudflare protection), accepted values are [chrome, firefox, opera, opera_gx, edge, chromium, brave, vivaldi, safari].
  -u WANTLIST_URLS [WANTLIST_URLS ...], --wantlist-urls WANTLIST_URLS [WANTLIST_URLS ...]
                        wantlist url(s) (if you pass multiples whislists, separate them with spaces)
  -m MAX_SELLERS, --max-sellers MAX_SELLERS
                        maximum number of sellers to display on the result page
  -w, --continue-on-warning
                        if specified the script will continue on non fatal errors
  -c, --articles-comment
                        if specified the sellers comments will be added to the result page
```

As you can see, you can call the script with one or more wantlist urls, and there is optional arguments available ([info on script arguments](https://github.com/BenSouchet/cw-wizard/blob/main/README.md#script-arguments)).

3. A basic example would be:
```shell
> python3 cw-wizard.py -b chrome -w https://www.cardmarket.com/en/Pokemon/Wants/10876807 -m 10
```
Example with multiple wantlists:
```shell
> python3 cw-wizard.py -b chrome -w https://www.cardmarket.com/en/Pokemon/Wants/10876807 https://www.cardmarket.com/en/Pokemon/Wants/10841970
```
4. If it's the first time you start the script your Cardmarket credentials will be asked to create a `credentials.json` file at the root of the project directory. For info on why credentials are required [read this section](https://github.com/BenSouchet/cw-wizard/edit/main/README.md#security-and-authentification).
<img width="598" alt="credentials_dialog" src="https://user-images.githubusercontent.com/17025808/159022712-b95ef3f5-0da6-4547-8f94-d49c0a4582ee.png">

5. With your favorite browser search for "my user agent" on Google and copy the value (Should start with: `Mozilla/5.0`)

6. When requested paste the value and press enter.

5. It's all, if everything goes well a result HTML page will open on your default web browser, otherwise check the terminal to see the error message(s).

### Script Arguments
With the command line version of the script you can use the following arguments:

| Argument Name | Description | Required |
|:-------------:|:-----------:|:--------:|
| `-v` *OR* `--version` | Display the version number of the script in your terminal. | No |
| `-h` *OR* `--help` | Display the help in your terminal. | No |
| `-b` *OR* `--browser-name` | Specify the browser you used to open a Cardmarket tab. | **Yes** |
| `-u` *OR* `--wantlist-urls` | One or more Cardmarket wantlists (wantlists) urls.<br />If you add multiple urls simply put a space between then (not a comma). | **Yes** |
| `-m` *OR* `--max-sellers` | The maximum number of sellers to display on the result page.<br />Default value `20`. `0` means display all. | No |
| `-w` *OR* `--continue-on-warning` | If specified the script won't stop on non fatal requests errors. | No |
| `-c` *OR* `--articles-comment` |If specified the script will retrieve and add sellers comments to the result page. | No |

## Version
Current version is `1.0.6`, you can download this latest release on the Releases category (on the sidebar), from [this page](https://github.com/BenSouchet/cw-wizard/releases) or `git clone` the `main` branch of the repository.

## Changelog

### 1.0.6
- Adding support for metacard in wantlists. Metacard is when a card is added to a wantlist without specifing the expansion (set to "Any").
- Adding sleep time between requests to avoid the too many requests error. (current sleep value is 170ms).

### 1.0.5
- Fixing issues with non english wantlist urls (for example urls with ".../fr/Pokémon/Wants/...").
- Adding a maximum of 6 resquests per card in wantlist (7 with the initial one) to avoid reaching Cardmarket user request limit to quickly due to one card settings.
- Fixing bugs with None object when loading more offers for cards.

### 1.0.4
- Update Cloudflare bypass, now require to specify your browser User-Agent to properly bypass retrictions.
- Fix price retrieve due to recent modification in the Cardmarket interface.
- Fix minor issues

### 1.0.3
- Bypassing newly added Cloudflare protection by using user cookies (thanks to package **Browser Cookie 3**).
- Apply platform specific user agent header ( #4 by @michasng )
- Fix attributes issue due to `isReverse` not always available. ( #5 )

### 1.0.1
- Handle more than the 50 first articles for the card pages (see function [`load_more_articles()`]()).
- Skip article and sellers that doesn't ship to your address.
- Extract and display sellers comments for articles (if script argument `-c` is specified).
- Add number or sales of the current seller when you display the cards list.
- Minors code simplification.

## Sorting Relevant Sellers
Currently the most relevant sellers are the ones with the most cards you are looking for in your wantlists.  
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
Since Cardmarket wantlists cannot be public this is required that you are logged in, so cards data can be retrieved.

This is why you credentials are required in order that the script work, if you aren't confident putting you credentials please review the code, since all the code is hosted here on Github you can see and check that nothing weird is done with your credentials.

As indicated at the beginning of this README, accounts with [Two-factor authentication (2FA)](https://en.wikipedia.org/wiki/Help:Two-factor_authentication) enabled won't be able to use this script, currently the feature is not planned to be added to the project.

## Origin of the Project
This project has been created because the exiting tools (provided by [Cardmarket](https://www.cardmarket.com/en/Pokemon/Wants/ShoppingWizard)) are good but somehow limited, with this open-souce script it's easy to get exactly the result wanted.  
If in the future, this project inspire others to create there own tools this would be a big success.

## Other Ressouces & Useful links
- [CardmarketToCSV](https://github.com/decdod/CardmarketToCSV) by [ddkod](https://github.com/decdod)
- [cm-wizard](https://github.com/michasng/cm-wizard) by [michasng](https://github.com/michasng)
- [Python Requests Documentation](https://docs.python-requests.org/en/latest/user/quickstart/)
- [Tillana Font](https://fonts.google.com/specimen/Tillana) by the [Indian Type Foundry](https://www.indiantypefoundry.com/) (License: [Open Font License](https://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=OFL))

## Contibutors
- [michasng](https://github.com/michasng)

## Author & maintainer
CW Wizard has been created and is currently maintained by [Ben Souchet](https://github.com/BenSouchet).

The code present in this repository is under [MIT license](https://github.com/BenSouchet/cw-wizard/blob/main/LICENSE).
