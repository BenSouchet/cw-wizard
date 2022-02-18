import re
import sys
import json
import logging
import requests
import argparse

from decimal import Decimal
from pathlib import Path
from bs4 import BeautifulSoup

VERSION = 0.1

LOG = None

EXIT_ERROR_MSG = 'The Wizard encountered issue(s) please check previous logs.\n'
EXIT_SUCCESS_MSG = 'The Wizard has finish is work, have a great day!\n'

# These two variables are extracted and set from the first wishlist url given to the script
CURR_LANG = 'en'
CURR_GAME = None

CARDMARKET_BASE_URL = 'https://www.cardmarket.com'

# This value can be overwriten via script arguments
MAXIMUM_SELLERS = 20

CARD_LANGUAGES =  { 'English': 1, 'French': 2, 'German': 3, 'Spanish': 4,
                    'Italian': 5, 'S-Chinese': 6, 'Japanese': 7,
                    'Portuguese': 8, 'Russian': 9, 'Korean': 10,
                    'T-Chinese': 11, 'Dutch': 12, 'Polish': 13, 'Czech': 14, 'Hungarian': 15 }

CARD_CONDITIONS = { 'Mint': 1, 'Near Mint': 2, 'Excellent': 3,
                    'Good': 4, 'Light Played': 5, 'Played': 6, 'Poor': 7, }

# These request errors description are from https://api.cardmarket.com/ws/documentation/API_2.0:Response_Codes
REQUEST_ERRORS  = { 307: ['Temporary Redirect', 'Particular requests can deliver thousands of entities (e.g. a large stock or requesting articles for a specified product, and many more). Generally all these request allow you to paginate the results - either returning a 206 or 204 HTTP status code. Nevertheless, all these requests can also be done without specifying a pagination. As general values for force-paginated requests please use maxResults=100 in order to avoid being 307\'d again. The first result is indexed with 0: start=0.'],
                    400: ['Bad Request', 'Whenever something goes wrong with your request, e.g. your POST data and/or structure is wrong, or you want to access an article in your stock by providing an invalid ArticleID, a 400 Bad Request HTTP status is returned, describing the error within the content.'],
                    401: ['Unauthorized', 'You get a 401 Unauthorized HTTP status, when authentication or authorization fails during your request, e.g. your Authorization (signature) is not correct.'],
                    403: ['Forbidden', 'You get a 403 Forbidden HTTP status, when you try to access valid resources, but don\'t have access to it, i. e. you try to access /authenticate with a dedicated or widget app, or resources specifically written for widget apps with a dedicated app.'],
                    404: ['Invalid request', 'The request isn\'t formatted correctly, request data and/or structure is wrong.'],
                    405: ['Not Allowed', 'You get a 405 Not Allowed HTTP status, every time you want to access a valid resource with a wrong HTTP method. While OPTIONS requests are now possible on all of the API\'s resources, most resources are limited to one or more other HTTP methods. These are always specified in the Access-Control-Allow-Methods header coming with each response. Please refer to CRUD Operations Documentation to learn more about the different HTTP methods and which purposes they fulfill in a RESTful API.'],
                    412: ['Precondition Failed', 'When you want to perform an invalid state change on one of your orders, e.g. confirm reception on an order, that\'s still not flagged as sent, you get a 412 Precondition Failed HTTP status.'],
                    417: ['Expectation Failed', 'Typically you get a 417 Expectation Failed HTTP status code, when your request has an XML body without the corresponding header and/or the body not sent as text, but its byte representation. Please also don\'t send any Expect: header with your request.'],
                    429: ['Too Many Requests', 'Our API has the following request limits which reset every midnight at 12am (0:00) CET/CEST: - Dedicated App (private users): 5.000 | - Dedicated App (commercial users): 100.000 | - Dedicated App (powerseller users): 1.000.000 | - Widget and 3rd-Party Apps don\'t have any request limits. If your has a request limit, additional response headers are sent by the API: - X-Request-Limit-Max, which contains your request limit, - X-Request-Limit-Count, which contains the actual number of requests you made after the last request limit reset. Once your request limit is reached the API will answer with a 429 Too Many Requests until the next request limit reset.']}

class ColoredFormatter(logging.Formatter):
    """Custom formatter handling color"""
    cyan = '\x1b[36;20m'
    green = '\x1b[32;20m'
    yellow = '\x1b[33;20m'
    red = '\x1b[31;20m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'
    message_format = '%(levelname)-8s - %(message)s'

    FORMATS = {
        logging.DEBUG: cyan + message_format + reset,
        logging.INFO: green + message_format + reset,
        logging.WARNING: yellow + message_format + reset,
        logging.ERROR: red + message_format + reset,
        logging.CRITICAL: bold_red + message_format + reset
    }

    def format(self, record):
        log_format = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_format)
        return formatter.format(record)

def init_logger():
    """Initialize script logger"""

    logger_name = Path(__file__).stem
    logger = logging.getLogger(logger_name)
    logger.setLevel(level = logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level=logging.DEBUG)
    console_handler.setFormatter(ColoredFormatter())

    logger.addHandler(console_handler)

    global LOG
    LOG = logger

def log_detailed_request_error(task, response):
    status_code = response.status_code
    LOG.error('Unable to {}. Request status code "{}":'.format(task, str(status_code)))

    # Check if we have more info on the request error
    status_code_info = REQUEST_ERRORS.get(status_code)
    if status_code_info:
        # Log the additional info
        LOG.error('{} -- {}'.format(status_code_info[0], status_code_info[1]))
    else:
        LOG.error('Unknown status code!')
    return None

def extract_log_in_error_msg(response):
    error_msg = ''

    # Step 1: Convert response to BeautifulSoup object
    soup = BeautifulSoup(response.text, 'html.parser')

    # Step 2: Try to find the error message in the HTML
    error_msg_container = soup.find('h4', class_='alert-heading')
    if error_msg_container:
        error_msg = error_msg_container.get_text('. ')

    return error_msg

def cardmarket_log_in(session, credentials):
    LOG.debug('Step 4: The Wizard start for you a temporary session on Cardmarket...')
    LOG.debug('  |____ This temp session isn\'t related to your browser, it\'s like private navigation session.')
    LOG.debug('  |____ No cookies will be stored/remains at the end.\n')

    # Step 1: Get the login page html (to retrieve the login token)
    response_get_login_page = session.get(CARDMARKET_BASE_URL + '/Login')
    if response_get_login_page.status_code != 200:
        # Issue with the request
        return log_detailed_request_error('access to Cardmarket', response_get_login_page)

    # Step 2: Extract the token from the html string
    regex_match = re.search(r'name="__cmtkn" value="(?P<token>\w+)"', response_get_login_page.text)
    if regex_match.lastindex is None:
        # Cannot retrieve the login token
        return LOG.error('Cannot retrieve the login token.')

    # Step 3: Prepare payload
    token = regex_match.group('token')
    referal_page_path = '/{}/{}'.format(CURR_LANG, CURR_GAME)
    payload = {'__cmtkn': token, 'referalPage': referal_page_path, 'username': credentials['login'], 'userPassword': credentials['password']}

    # Step 4: Do the log-in POST request to Cardmarket with the payload
    response_post_login = session.post('{}/{}/{}/PostGetAction/User_Login'.format(CARDMARKET_BASE_URL, CURR_LANG, CURR_GAME), data=payload)
    if response_post_login.status_code != 200:
        # Issue with the request
        return log_detailed_request_error('log-in to Cardmarket', response_get_login_page)

    # Step 5: Check in the response HTML if there is a log-in rror
    log_in_error_msg = extract_log_in_error_msg(response_post_login)
    if log_in_error_msg:
        # It's most likely an issue with the payload (wrong username and/or password)
        return LOG.error('Unable to log-in to Cardmarket. Message: {}.'.format(log_in_error_msg))

    LOG.info('Successfully logged in !\n')

    return True

def cardmarket_log_out(session):
    LOG.debug('Step 8: The Wizard log out of the temporary session on Cardmarket...\n')

    response_get_logout = session.get('{}/{}/{}/PostGetAction/User_Logout'.format(CARDMARKET_BASE_URL, CURR_LANG, CURR_GAME))
    if response_get_logout.status_code != 200:
        # Issue with the request
        return log_detailed_request_error('logout of Cardmarket', response_get_logout)
    LOG.info('Successfully logout!')

def retrieve_wishlist(session, wishlist_url):
    LOG.debug('  |____ The Wizard is retrieving the wishlist ("{}")...'.format(wishlist_url))

    wishlist = None

    # Step 1: Get the desired wishlist page
    response_get_wishlist = session.get(wishlist_url)
    if response_get_wishlist.status_code != 200:
        # Issue with the request
        return log_detailed_request_error('access to the wishlist ("{}")'.format(wishlist_url), response_get_wishlist)

    # Step 2: Convert response to BeautifulSoup object
    soup = BeautifulSoup(response_get_wishlist.text, 'html.parser')

    # Step 3: Retrieve the wishlist title
    wishlist_title = soup.find('h1').string

    # Step 4: Retrieve the wishlist table (BeautifulSoup object)
    wishlist_section = soup.find(id='WantsListTable')
    if not wishlist_section:
        LOG.warning('The wishlist seems to be empty, or the cards list could\'nt be retrieved')
        return False

    wishlist_table = wishlist_section.table.tbody
    column_index = { 'name': 3, 'languages': 5, 'minCondition': 6, 'isReverse': 7,
                    'isSigned': 8, 'isFirstEd': 9, 'isAltered': 10,'maxPrice': 11 }

    # Step 5: Convert the wishlist table to python list
    card_count = len(wishlist_table.contents)
    card_count_str = '{} card{}'.format(str(card_count), 's' if card_count > 1 else '')
    wishlist = [ '{} ({})'.format(wishlist_title, card_count_str), wishlist_url ]
    for row in wishlist_table.children:
        card = {}

        # Step 5.A: Retrieve and add attributes to the card dict
        name_link_tag = row.contents[column_index['name']].a
        card['url'] = CARDMARKET_BASE_URL + name_link_tag['href'].split('?')[0]
        card['title'] = name_link_tag.contents[0]

        card['languages'] = []
        languages_link_tags = row.contents[column_index['languages']].find_all('a')
        for languages_link_tag in languages_link_tags:
            card['languages'].append(languages_link_tag.span['data-original-title'])

        for attribute in ['minCondition', 'isReverse', 'isSigned', 'isFirstEd', 'isAltered']:
            card[attribute] = row.contents[column_index[attribute]].find('span', class_='sr-only').contents[0]

        card['maxPrice'] = row.contents[column_index['maxPrice']].span.contents[0]
        # If maxPrice is a value we convert it into a Decimal
        if card['maxPrice'] != 'N/A':
            card['maxPrice'] = Decimal(card['maxPrice'].split(' ')[0].replace('.','').replace(',','.'))

        # Step 5.B: Add newly created card dict to the wishlish array
        wishlist.append(card)

    return wishlist

def populate_sellers_dict(session, sellers, wishlist, continue_on_error=False):
    wishlist_url = wishlist.pop(0)
    LOG.debug('  |____ The Wizard is aggregating sellers and articles data for the wishlist ("{}")...'.format(wishlist_url))

    for card in wishlist:
        # If multiple languages selected with do one request per language
        for card_language in card['languages']:
            # Save a sellers list for the current card,
            # to avoid adding multiple time the same article for a seller
            # in case a seller sell the card multiple times in different conditions
            card_sellers_names = []

            # Step 1: Create the get params for the request according to card attributes
            params = {}
            params['language'] = CARD_LANGUAGES[card_language]
            params['minCondition'] = CARD_CONDITIONS[card['minCondition']]
            for attribute in ['isReverse', 'isSigned', 'isFirstEd', 'isAltered']:
                if card[attribute] != 'Any':
                    params[attribute] = card[attribute]

            # Step 2: Get the card page
            response_get_card_articles = session.get(card['url'], params=params)
            if response_get_card_articles.status_code != 200:
                # Issue with the request
                log_detailed_request_error('access the card page ("{}")'.format(card['title']), response_get_card_articles)
                if continue_on_error:
                    continue
                return None

            card_full_url = response_get_card_articles.url

            # Step 3: Retrieve the articles table (BeautifulSoup object)
            soup = BeautifulSoup(response_get_card_articles.text, 'html.parser')
            articles_table = soup.find('div', class_='table-body')

            # Step 4: Iterate over articles
            for article in articles_table.children:
                # Check if this is a proper article
                if 'article-row' not in article.attrs['class']:
                    LOG.warning('No offers found for card ("{}") with parameters: {} {}.'.format(card['title'], params, card['maxPrice']))
                    break

                seller_name_tag = article.find('span', class_='seller-name').find('a')
                seller_name = seller_name_tag.contents[0]

                # Step 4.A: Skip if we already added an article (of this card) for this seller
                if seller_name in card_sellers_names:
                    # Skip this article
                    continue

                seller_profile_url = CARDMARKET_BASE_URL + seller_name_tag['href']

                price_str = article.find('div', class_='price-container').find('span', class_='text-right').contents[0]
                price = Decimal(price_str.split(' ')[0].replace('.','').replace(',','.'))
                # Step 4.B: Check if price isn't above maxPrice
                if isinstance(card['maxPrice'], Decimal) and price > card['maxPrice']:
                    # The current article price is superior than the max price
                    # we stop iterate over article (article are listed according to price)
                    break

                # Step 4.C: Create the new article
                article_attributes = article.find('div', class_='product-attributes')
                article_condition = article_attributes.a.span.contents[0]
                article_language = article_attributes.find('span', class_='icon')['data-original-title']
                article = { 'name': card['title'], 'url': card_full_url, 'language': article_language, 'condition': article_condition, 'price': price }

                # Step 4.D: Add this article on the seller key in the dict
                if seller_name in sellers:
                    sellers[seller_name]['cards'].append(article)
                else:
                    sellers[seller_name] = {'url': seller_profile_url, 'cards': [ article ] }

                # Step 4.E: Add seller name in the corresponding list
                card_sellers_names.append(seller_name)

    return sellers

def determine_relevant_sellers(sellers, max_sellers):
    LOG.debug('Step 6: The Wizard is sorting sellers to find relevant ones...')

    if not sellers:
        return LOG.warning('  |____ It\'s seems there is no seller.')

    sorted_list = []
    # Step 1: Sort sellers dict according to number of articles
    for seller_name, data in sellers.items():
        total_price = Decimal(0.0)
        for article in data['cards']:
            total_price += article['price']
        sorted_list.append((seller_name, len(data['cards']), str(total_price)))

    from operator import itemgetter
    sorted_list = sorted(sorted_list,key=itemgetter(1), reverse=True)

    # Step 2: reduce sellers list
    relevant_sellers = sorted_list[:max_sellers]

    return relevant_sellers

def delete_previous_result_page(path_file):
    """Delete a file"""

    if path_file and path_file.exists():
        try:
            if path_file.is_file():
                LOG.debug('  |____ Deleting the previous result page...')
                import os
                os.remove(path_file)
        except Exception as e:
            LOG.error('Failed to delete "{}". Reason: {}'.format(path_file, e))
            return False
    return True

def build_result_page(wishlists_info, max_sellers, sellers, relevant_sellers):
    LOG.debug('Step 7: The Wizard is creating a beautiful result page...')

    # Step 1: Retrieve content of template.html
    soup = None
    template_path = Path.cwd().joinpath('assets', 'template.html')
    try:
        with open(template_path, 'r', encoding='utf-8') as template_file:
            template_contents = template_file.read()
            soup = BeautifulSoup(template_contents, 'html.parser')
    except IOError as err:
        LOG.error('Template file "{}" cannot be properly opened.'.format(template_path))
        return LOG.error(err)

    # Step 2: Edit the template
    # Step 2.A: Add "max_sellers" value
    max_sellers_parent_tag = soup.find('span', id='max-sellers-value')
    max_sellers_parent_tag.string = str(max_sellers)

    # Step 2.B: Add Wishlists
    wishlists_parent_tag = soup.find('div', id='wishlist-links')
    wishlists_links_html_str = ''
    for wishlist_info in wishlists_info:
        wishlists_links_html_str += '<a class="wishlist-item button" href="{}" target="_blank" rel="noopener noreferrer">{}</a>'.format(wishlist_info[0], wishlist_info[1])
    wishlists_parent_tag.append(BeautifulSoup(wishlists_links_html_str, 'html.parser'))

    # Step 2.C: Retrieve containers tags and declare variables for relevant sellers
    sellers_parent_tag = soup.find('div', id='relevant-sellers-items')
    sellers_html_str = ''

    sellers_cards_lists_parent_tag = soup.find('div', id='sellers-cards-lists')
    sellers_cards_lists_html_str = ''

    # Step 2.D: Create HTML contents for relevant sellers
    seller_index = 0
    for relevant_seller in relevant_sellers:
        index_5_digits_str = '{:05}'.format(seller_index)
        sellers_html_str += '<div class="seller-item"><a href="{}" id="seller-{}" class="seller-name" target="_blank" rel="noopener noreferrer">{}</a><hr><span class="number-cards">Cards: <b>{}</b></span><span class="total-price">Total: {} €</span><a href="#" onclick="showCardsList(\'{}\'); return false;" class="link-cards-list button">See Cards ></a></div>'.format(sellers[relevant_seller[0]]['url'], index_5_digits_str, relevant_seller[0], str(relevant_seller[1]), str(relevant_seller[2]), index_5_digits_str)
        # Concatenate cards list
        sellers_cards_lists_html_str += '<div id="seller-{}-cards" class="cards-list">'.format(index_5_digits_str)
        for card in sellers[relevant_seller[0]]['cards']:
            sellers_cards_lists_html_str += '<div class="card-item"><span class="card-condition {}">{}</span><span class="card-language {}"></span><a href="{}" class="card-title" target="_blank" rel="noopener noreferrer">{}</a><span class="card-price">{} €</span></div>'.format(card['condition'], card['condition'], card['language'], card['url'], card['name'], card['price'])
        sellers_cards_lists_html_str += '</div>'

        seller_index += 1

    # Step 2.E: Append HTML for relevant sellers
    sellers_parent_tag.append(BeautifulSoup(sellers_html_str, 'html.parser'))
    sellers_cards_lists_parent_tag.append(BeautifulSoup(sellers_cards_lists_html_str, 'html.parser'))

    # Step 3: Save as "result.html" in current project directory
    result_path = Path.cwd().joinpath('result.html')
    # Step 3.A: if "result.html" exists delete it
    success = delete_previous_result_page(result_path)
    if not success:
        return False
    LOG.debug('  |____ Saving the result page...\n')
    # Step 3.B: Create and write to the file
    try:
        with open(result_path, 'w+', encoding='utf-8') as result_file:
            result_file.write(str(soup))
    except IOError as err:
        LOG.error('Error while creating the result file ("{}").'.format(result_path))
        return LOG.error(err)

    LOG.info('The result page has been created here: "{}"\n'.format(result_path.as_uri()))

    # Step 4: Open the result page
    import webbrowser
    try:
        webbrowser.open(result_path.as_uri())
    except webbrowser.Error:
        # Since it's not critical at all only display a warning.
        LOG.warning('Failed to automatically open the result page for you.')

    return True

def cardmarket_wishlist_wizard(credentials, wishlist_urls, continue_on_error, max_sellers):
    LOG.debug('Step 3: Calling the Wizard...\r\n')

    end_intro_message = 'these whislists urls!' if len(wishlist_urls) > 1 else 'this wishlist url!'
    LOG.info('Hi there... You are here to find great card deals, right? Humm... okay... Give me {}'.format(end_intro_message))
    LOG.warning('Be aware that he\'s very old and can be sometimes grumpy and slow to perform all these tasks.\r\n')

    # Step 1: Create a web session (to be able to stay connected)
    with requests.Session() as session:
        # Step 2: Log-in to Cardmarket
        success = cardmarket_log_in(session, credentials)
        if not success:
            # Param "stop_on_error" is ignored since it's a FATAL error we cannot skip log in
            return False

        sellers = {}
        error_occured = False
        wishlists_info = []
        LOG.debug('Step 5: Handling the wishlist(s)')
        for wishlist_url in wishlist_urls:
            # Step 2: Retrieve wishlist in JSON
            wishlist = retrieve_wishlist(session, wishlist_url)
            if wishlist is False:
                # Empty wishlist
                continue
            elif wishlist is None:
                error_occured = True
                if continue_on_error:
                    # Skip to next wishlist
                    continue
                # Only break, not return so we can still log out of Cardmarket
                break

            # Step 2.A: Add info to the wishlists_info list
            wishlists_info.append((wishlist_url, wishlist.pop(0)))

            # Step 3: Populate the sellers dictionary
            populate_sellers_dict(session, sellers, wishlist, continue_on_error)

        # Step 4: Display most relevant sellers
        if not error_occured or continue_on_error:
            relevant_sellers = determine_relevant_sellers(sellers, max_sellers)

            success = build_result_page(wishlists_info, max_sellers, sellers, relevant_sellers)
            if not success:
                error_occured = True

        # Step 5: Logout from Cardmarket, simply a safety mesure.
        cardmarket_log_out(session)

    return not error_occured

def get_credentials_from_file(credentials_path):
    LOG.debug('Step 2: Retrieving credentials...')

    credentials = None

    # Step 1: Check if the path point to an existing file
    if not credentials_path.exists():
        # File not found
        LOG.error('file \'credentials.json\' doesn\'t exists in the current directory.')
        return False

    # Step 2: Open the file as JSON
    try:
        with open(credentials_path, 'r', encoding='utf-8') as json_file:
            credentials = json.load(json_file)
    except json.JSONDecodeError as err:
        return LOG.error('Issue(s) in the JSON file: {} (line {} pos {}).'.format(err.msg, err.lineno, err.pos))
    except IOError as err:
        LOG.error('Credentials file "{}" cannot be properly opened.'.format(credentials_path))
        LOG.error(err)
        return None

    # Step 3: Check if the JSON object contains the necessary keys and values
    #         And the values are strings
    keys_to_check = ['login', 'password']
    for key in keys_to_check:
        if key not in credentials:
            return LOG.error('Key "{}" not present in the credentials JSON file "{}".'.format(key, credentials_path))
        if not credentials[key] or not isinstance(credentials[key], str):
            return LOG.error('Value of key "{}" isn\'t of type string in the credentials JSON file "{}".'.format(key, credentials_path))

    return credentials

def get_credentials_user_inputs(credentials_path):
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
        return LOG.error('Script cannot proceed without the credentials file.')

    # Step 2: Ask for the login
    credentials['login'] = input('Enter your Cardmarket login: ')

    # Step 2: Ask for the login
    credentials['password'] = getpass.getpass('Enter your Cardmarket password: ')

    # Step 3: Create the JSON file and dump credentials
    with open(credentials_path, 'w+', encoding='utf-8') as json_file:
        json.dump(credentials, json_file, indent=4, ensure_ascii=False)
    LOG.info('Credentials file successfully created ("{}")'.format(credentials_path))

    return credentials

def check_input_parameters_and_set_global_info(wishlist_urls, max_sellers):
    LOG.debug('Step 1: Checking inputs parameters...')

    # Declare variables to store values that will be at the end set to GLOBAL variables
    global_language = None
    global_game = None

    # Step 1: Check the wishlist urls
    error_occured = False
    for wishlist_url in wishlist_urls:
        if not isinstance(wishlist_url, str):
            LOG.error('Wishlist url need to be of type string.')
            error_occured = True
        matched = re.match(r'^https:\/\/www\.cardmarket\.com\/(\w{2})\/(\w+)\/Wants\/\d+$', wishlist_url)
        if not matched:
            LOG.error('Invalid wishlist url ("{}"), valid pattern is:'.format(wishlist_url))
            LOG.error(CARDMARKET_BASE_URL + '/<LANGUAGE_CODE>/<GAME_NAME>/Wants/<WISHLIST_CODE>')
            error_occured = True
            continue
        if not global_game:
            (global_language, global_game) = matched.groups()
    if error_occured:
        return False

    # Step 2: Check value of "max_sellers"
    if max_sellers < 0:
        return LOG.error('Input parameter "max_sellers" need to be an int superior to 0.')
    elif max_sellers == 0 or max_sellers > 300:
        LOG.warning('Value of input parameter "max_sellers" is set to "{}", caution this means the process can be long and the result page can be heavy.'.format(max_sellers))

    # Step 3: Check validity of global info
    if not global_language or len(global_language) != 2 or not global_language.islower():
        return LOG.error('The language code in one of the wishlist url isn\'t formated correctly, need to be 2 character long, only lowercase.')
    # Since new games can be added to Cardmarket, checking "global_game" is not worth it

    # Step 4: Assign info to global variables
    global CURR_LANG
    global CURR_GAME
    CURR_LANG = global_language
    CURR_GAME = global_game

    return True

def main(wishlist_urls, continue_on_error, max_sellers):
    """Entry point of the CW Wizard script"""

    # Step 1: Setup a logger for the current script to log usefull info in the console
    init_logger()

    # Step 2: Check input parameters before calling the Wizard
    #         Also retrieve the language and the game name
    success = check_input_parameters_and_set_global_info(wishlist_urls, max_sellers)
    if not success:
        return LOG.error(EXIT_ERROR_MSG)

    # Step 3: Retrieve credentials
    credentials_path = Path.cwd().joinpath('credentials.json')
    credentials = get_credentials_from_file(credentials_path)
    if credentials is False:
        # The file doesn't exists
        LOG.warning('Required local file "credentials.json" not found.')
        credentials = get_credentials_user_inputs(credentials_path)
    if credentials is None:
        return LOG.error(EXIT_ERROR_MSG)

    # Step 4: Call the Wizard
    success = cardmarket_wishlist_wizard(credentials, wishlist_urls, continue_on_error=continue_on_error, max_sellers=max_sellers)

    if not success:
        return LOG.error(EXIT_ERROR_MSG)

    LOG.info(EXIT_SUCCESS_MSG)
    return success

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='CW Wizard', description='CW Wizard, Find the best bundles for the cards in your wishlist(s).')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s '+str(VERSION))
    parser.add_argument('-w', '--wishlist-urls', nargs='+', required=True, type=str, action='extend', help='wishlist url(s) (if you pass multiples whislists, separate them with spaces)')
    parser.add_argument('-m', '--max-sellers', type=int, default=MAXIMUM_SELLERS, help='maximum number of sellers to display on the result page')
    parser.add_argument('-c', '--continue-on-error', action='store_true', help='if specified the script will continue on non fatal errors')

    arguments = parser.parse_args()

    main(arguments.wishlist_urls, arguments.continue_on_error, arguments.max_sellers)
