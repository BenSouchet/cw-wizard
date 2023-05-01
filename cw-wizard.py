from core import SCRIPT_NAME, VERSION, MAXIMUM_SELLERS
from core import EXIT_SUCCESS_MSG, EXIT_ERROR_MSG
from core import LOG
from core import FunctResult
from core import create_credentials_file
from core import get_credentials_from_file
from core import check_credentials_validity
from core import get_formatted_browser_name
from core import check_wantlists_and_max_sellers
from core import cardmarket_wantlist_wizard

def get_credentials_user_inputs():
    funct_result = FunctResult()

    import getpass

    credentials = {}
    question = 'Do you want to create the file ?'

    # Step 1: Ask if user when to create the credentials JSON file
    create_the_file = None
    while create_the_file is None:
        reply = str(input(question + ' (y/n): ')).lower().strip()[:1]
        if reply == 'y':
            create_the_file =  True
        elif reply == 'n':
            create_the_file =  False
        else:
            question = 'Unrecognize anwser, please enter'

    if not create_the_file:
        funct_result.addError('Script cannot proceed without the credentials file.')
        return funct_result

    # Step 2: Ask for the login
    credentials['login'] = input('Enter your Cardmarket login: ')

    # Step 2: Ask for the login
    credentials['password'] = getpass.getpass('Enter your Cardmarket password: ')

    create_credentials_file(credentials)

    funct_result.addResult(credentials)

    return funct_result

def main(browser_name, wantlist_urls, continue_on_warning, max_sellers, articles_comment):
    """Entry point of the CW Wizard script"""

    # Step 1: Check input parameters before calling the Wizard
    #         Also retrieve the language and the game name
    result = get_formatted_browser_name(browser_name)
    result.logMessages()
    if not result.isValid():
        return LOG.error(EXIT_ERROR_MSG)

    # Set the reformatted browser_name
    browser_name = result.getResult()

    result = check_wantlists_and_max_sellers(wantlist_urls, max_sellers)
    result.logMessages()
    if not result.isValid():
        return LOG.error(EXIT_ERROR_MSG)

    # Step 2: Retrieve credentials
    result = get_credentials_from_file()
    result.logMessages()

    credentials = None
    if result.isValid():
        # Check the credentials are valid
        credentials = result.getResult()
        if 'skip-check' not in credentials:
            result = check_credentials_validity(browser_name, credentials, silently=True)
            result.logMessages()
        # Since we have maybe check the validity, perform a second check on the result object
        if result.isValid():
            credentials = result.getResult()

    if not credentials:
        # File not found, ask the user if he want to create the file
        result = get_credentials_user_inputs()
        result.logMessages()

        if result.isValid():
            credentials = result.getResult()

    if not credentials:
        return LOG.error(EXIT_ERROR_MSG)

    # Step 3: Call the Wizard
    result = cardmarket_wantlist_wizard(browser_name, credentials, wantlist_urls, continue_on_warning=continue_on_warning, max_sellers=max_sellers, articles_comment=articles_comment)
    result.logMessages()

    if not result.isValid():
        return LOG.error(EXIT_ERROR_MSG)

    LOG.info(EXIT_SUCCESS_MSG)
    return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(prog=SCRIPT_NAME, description='{} v{}, Find the best bundles for the cards in your wantlist(s).'.format(SCRIPT_NAME, VERSION))
    parser.add_argument('-v', '--version', action='version', version='%(prog)s '+ VERSION)
    parser.add_argument('-b', '--browser_name', type=str, required=True, help='Specify the browser name you used to open the Cardmarket tab (needed to bypass Cloudflare protection), accepted values are [chrome, firefox, opera, opera_gx, edge, chromium, brave, vivaldi, safari].')
    parser.add_argument('-u', '--wantlist-urls', nargs='+', required=True, type=str, action='extend', help='wantlist url(s) (if you pass multiples whislists, separate them with spaces)')
    parser.add_argument('-m', '--max-sellers', type=int, default=MAXIMUM_SELLERS, help='maximum number of sellers to display on the result page')
    parser.add_argument('-w', '--continue-on-warning', action='store_true', help='if specified the script will continue on non fatal errors')
    parser.add_argument('-c', '--articles-comment', action='store_true', help='if specified the sellers comments will be added to the result page')

    arguments = parser.parse_args()

    main(arguments.browser_name, arguments.wantlist_urls, arguments.continue_on_warning, arguments.max_sellers, arguments.articles_comment)
