import re
import sys
import json
import base64
import logging
import requests

from decimal import Decimal
from pathlib import Path
from bs4 import BeautifulSoup

SCRIPT_NAME = 'CW Wizard'

VERSION = '1.0.1'

EXIT_ERROR_MSG = 'The Wizard encountered issue(s) please check previous logs.\n'
EXIT_SUCCESS_MSG = 'The Wizard has finish is work, have a great day!\n'

# These two variables are extracted and set from the first wantlist url given to the script
CURR_LANG = 'en'
CURR_GAME = 'Magic'

CARDMARKET_BASE_URL = 'https://www.cardmarket.com'
CARDMARKET_BASE_URL_REGEX = r'^https:\/\/www\.cardmarket\.com'

# This value can be overwriten via script arguments or via GUI
MAXIMUM_SELLERS = 20

CARD_LANGUAGES =  { 'English': 1, 'French': 2, 'German': 3, 'Spanish': 4,
                    'Italian': 5, 'S-Chinese': 6, 'Japanese': 7,
                    'Portuguese': 8, 'Russian': 9, 'Korean': 10,
                    'T-Chinese': 11, 'Dutch': 12, 'Polish': 13, 'Czech': 14, 'Hungarian': 15 }

CARD_CONDITIONS = { 'Mint': 1, 'Near Mint': 2, 'Excellent': 3,
                    'Good': 4, 'Light Played': 5, 'Played': 6, 'Poor': 7, }

CARD_CONDITIONS_SHORTNAMES = {  'Mint': 'MT', 'Near Mint': 'NM', 'Excellent': 'EX',
                                'Good': 'GD', 'Light Played': 'LP', 'Played': 'PL', 'Poor': 'PO', }

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

CREDENTIALS_PATH = Path.cwd().joinpath('credentials.json')

class FunctResult():
    def __init__(self):
        self.status = 'valid'
        self.messages = []
        self.result = None

    def addWarning(self, message):
        if self.status == 'valid':
            self.status = 'warning'
        self.messages.append({ 'type': 'warning', 'content': message, 'logged': False })

    def addError(self, message):
        self.status = 'error'
        self.messages.append({ 'type': 'error', 'content': message, 'logged': False })

    def addDetailedRequestError(self, task, response, as_warning=False):
        status_code = response.status_code
        message = 'Unable to {}. Request status code "{}":'.format(task, str(status_code))

        # Check if we have more info on the request error
        status_code_info = REQUEST_ERRORS.get(status_code)
        detailed_message = 'Unknown status code!'
        if status_code_info:
            # Log the additional info
            detailed_message = '{} -- {}'.format(status_code_info[0], status_code_info[1])

        if as_warning:
            self.addWarning(message)
            self.addWarning(detailed_message)
        else:
            self.addError(message)
            self.addError(detailed_message)

    def append(self, result):
        if result.status == 'error':
            self.status = 'error'
        if result.status == 'warning' and self.status == 'valid':
            self.status = 'warning'
        self.messages = [*self.messages, *result.messages]

    def setResult(self, element):
        self.result = element

    def addResult(self, element):
        if not self.result:
            self.result = element
        elif isinstance(self.result, list):
            self.result.append(element)
        else:
            self.result = [self.result, element]

    def getResult(self):
        return self.result

    def isWarning(self):
        return self.status == 'warning'

    def isValid(self):
        return self.status == 'valid'

    def logMessages(self):
        for message in self.messages:
            if not message['logged']:
                method = getattr(LOG, message['type'])
                method(message['content'])
                message['logged'] = True

    def getMessages(self, message_type='all'):
        messages = []
        for message in self.messages:
            if message_type != 'all' and message['type'] == message_type:
                messages.append(message)

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

    return logger

LOG = init_logger()

def extract_log_in_error_msg(response):
    error_msg = ''

    # Step 1: Convert response to BeautifulSoup object
    soup = BeautifulSoup(response.text, 'html.parser')

    # Step 2: Try to find the error message in the HTML
    error_msg_container = soup.find('h4', class_='alert-heading')
    if error_msg_container:
        error_msg = error_msg_container.get_text('. ')

    return error_msg

def cardmarket_log_in(session, credentials, silently=False):
    funct_result = FunctResult()

    if not silently:
        LOG.debug('------- The Wizard start for you a temporary session on Cardmarket...')
        LOG.debug('  |____ This temp session isn\'t related to your browser, it\'s like private navigation session.')
        LOG.debug('  |____ No cookies will be stored/remains at the end.\n')

    # Step 1: Get the login page html (to retrieve the login token)
    response_get_login_page = session.get(CARDMARKET_BASE_URL + '/Login')
    if response_get_login_page.status_code != 200:
        # Issue with the request
        funct_result.addDetailedRequestError('access to Cardmarket', response_get_login_page)
        return funct_result

    # Step 2: Extract the token from the html string
    regex_match = re.search(r'name="__cmtkn" value="(?P<token>\w+)"', response_get_login_page.text)
    if regex_match.lastindex is None:
        # Cannot retrieve the login token
        funct_result.addError('Cannot retrieve the login token.')
        return funct_result

    # Step 3: Prepare payload
    token = regex_match.group('token')
    referal_page_path = '/{}/{}'.format(CURR_LANG, CURR_GAME)
    payload = {'__cmtkn': token, 'referalPage': referal_page_path, 'username': credentials['login'], 'userPassword': credentials['password']}

    # Step 4: Do the log-in POST request to Cardmarket with the payload
    response_post_login = session.post('{}/{}/{}/PostGetAction/User_Login'.format(CARDMARKET_BASE_URL, CURR_LANG, CURR_GAME), data=payload)
    if response_post_login.status_code != 200:
        # Issue with the request
        funct_result.addDetailedRequestError('log-in to Cardmarket', response_get_login_page)
        return funct_result

    # Step 5: Check in the response HTML if there is a log-in rror
    log_in_error_msg = extract_log_in_error_msg(response_post_login)
    if log_in_error_msg:
        # It's most likely an issue with the payload (wrong username and/or password)
        funct_result.addError('Unable to log-in to Cardmarket. Message: {}.'.format(log_in_error_msg))
        return funct_result

    if not silently:
        LOG.info('Successfully logged in !\n')

    return funct_result

def cardmarket_log_out(session, silently=False):
    funct_result = FunctResult()

    if not silently:
        LOG.debug('------- The Wizard log out of the temporary session on Cardmarket...\n')

    response_get_logout = session.get('{}/{}/{}/PostGetAction/User_Logout'.format(CARDMARKET_BASE_URL, CURR_LANG, CURR_GAME))
    if response_get_logout.status_code != 200:
        # Issue with the request
        funct_result.addDetailedRequestError('logout of Cardmarket', response_get_logout)
        return funct_result

    if not silently:
        LOG.info('Successfully logout!')

    return funct_result

def retrieve_wantlist(session, wantlist_url, continue_on_warning=False):
    funct_result = FunctResult()

    LOG.debug('  |____ The Wizard is retrieving the wantlist ("{}")...'.format(wantlist_url))

    wantlist = None

    # Step 1: Get the desired wantlist page
    response_get_wantlist = session.get(wantlist_url)
    if response_get_wantlist.status_code != 200:
        # Issue with the request
        funct_result.addDetailedRequestError('access to the wantlist ("{}")'.format(wantlist_url), response_get_wantlist, continue_on_warning)
        return funct_result

    # Step 2: Convert response to BeautifulSoup object
    soup = BeautifulSoup(response_get_wantlist.text, 'html.parser')

    # Step 3: Retrieve the wantlist title
    wantlist_title = soup.find('h1').string

    # Step 4: Retrieve the wantlist table (BeautifulSoup object)
    wantlist_section = soup.find(id='WantsListTable')
    if not wantlist_section:
        funct_result.addWarning('The wantlist seems to be empty, or the cards list could\'nt be retrieved')
        return funct_result

    wantlist_table = wantlist_section.table.tbody
    column_index = { 'name': 3, 'languages': 5, 'minCondition': 6, 'isReverse': 7,
                    'isSigned': 8, 'isFirstEd': 9, 'isAltered': 10,'maxPrice': 11 }

    # Step 5: Convert the wantlist table to python list
    card_count = len(wantlist_table.contents)
    card_count_str = '{} card{}'.format(str(card_count), 's' if card_count > 1 else '')
    wantlist = [ '{} ({})'.format(wantlist_title, card_count_str), wantlist_url ]
    for row in wantlist_table.children:
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
        wantlist.append(card)

    funct_result.addResult(wantlist)
    return funct_result

def _get_load_more_args(card, product_id):
    args_dict = { 'page': '0' }
    filter_settings = {}
    filter_settings['idLanguage'] = {str(CARD_LANGUAGES[language]): CARD_LANGUAGES[language] for language in card['languages']}
    for attribute in ['isReverse', 'isSigned', 'isFirstEd', 'isAltered']:
        if card[attribute] != 'Any':
            filter_settings[attribute] = card[attribute]
    condition = [shortname for shortname in CARD_CONDITIONS_SHORTNAMES.values()]
    if card['minCondition'] != 'Poor':
        condition = condition[:condition.index(CARD_CONDITIONS_SHORTNAMES[card['minCondition']]) + 1]
    filter_settings['condition'] = condition
    args_dict['filterSettings'] = json.dumps(filter_settings, separators=('\\,', ':'))
    args_dict['idProduct'] = product_id

    return args_dict

def _get_load_more_product_id(load_more_btn):
    onclick_str = load_more_btn['onclick']
    return re.search(r'\'idProduct\'\:\'(?P<product_id>\d+)\'', onclick_str).group('product_id')

def _get_load_more_request_token(load_more_btn):
    onclick_str = load_more_btn['onclick']
    return re.match(r'jcp\(\'(?P<token>[A-Z0-9%]+)\'', onclick_str).group('token')

def load_more_articles(session, funct_result, soup, card, articles_table):
    # Step 1: Check if there isn't a load more articles button, in this case we stop
    load_more_btn = soup.find(id='loadMoreButton')
    if not load_more_btn:
        return None

    # Step 2: Initialize variables
    active = True
    card_curr_game = re.match(CARDMARKET_BASE_URL_REGEX + r'\/\w{2}\/(\w+)', card['url']).group(1)
    product_id = _get_load_more_product_id(load_more_btn)
    load_more_args = _get_load_more_args(card, product_id)
    request_token = _get_load_more_request_token(load_more_btn)

    # Step 3: Retrieve more article until card['maxPrice'] is reached or there is no more article to load
    while active:
        # Step 3.A: Get the price of the last card currently displayed
        last_article = articles_table.contents[-1]
        last_article_price_str = last_article.find('div', class_='price-container').find('span', class_='text-right').contents[0]
        last_article_price = Decimal(last_article_price_str.split(' ')[0].replace('.','').replace(',','.'))

        # Step 3.B: Check if we need to load more articles, if yes send a new request to get more articles.
        if last_article_price <= card['maxPrice']:
            # Step 3.B.I: Initialize a payload and do a POST request
            args_base64 = base64.b64encode(bytes(json.dumps(load_more_args, separators=(',', ':')), 'utf-8'))
            payload = {'args': request_token + args_base64.decode("utf-8")}
            response_post_load_article = session.post('{}/{}/{}/AjaxAction'.format(CARDMARKET_BASE_URL, CURR_LANG, card_curr_game), data=payload)
            if response_post_load_article.status_code != 200:
                # Issue with the request
                funct_result.addWarning('Failed to load more articles for card page ("{}")'.format(card['title']))
                # We cannot retrieve more articles, so break the loop
                break

            # Step 3.B.II: Handle the request result containing the new articles and the new page_index value
            more_article_soup = BeautifulSoup(response_post_load_article.text, 'html.parser')
            load_more_args['page'] = int(more_article_soup.find('newpage').contents[0])

            articles_rows_html_str = base64.b64decode(more_article_soup.find('rows').contents[0]).decode("utf-8")
            articles_table.append(BeautifulSoup(articles_rows_html_str, 'html.parser'))
            if load_more_args['page'] < 0:
                # There is no more article available, stop the process
                active = False
        else:
            active = False

def populate_sellers_dict(session, sellers, wantlist, articles_comment=False, continue_on_warning=False):
    funct_result = FunctResult()

    wantlist_url = wantlist.pop(0)
    LOG.debug('  |____ The Wizard is aggregating sellers and articles data for the wantlist ("{}")...'.format(wantlist_url))

    for card in wantlist:
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
                funct_result.addDetailedRequestError('access the card page ("{}")'.format(card['title']), response_get_card_articles, continue_on_warning)
                if continue_on_warning:
                    continue
                return funct_result

            card_full_url = response_get_card_articles.url

            # Step 3.A: Retrieve the articles table (BeautifulSoup object)
            soup = BeautifulSoup(response_get_card_articles.text, 'html.parser')
            articles_table = soup.find('div', class_='table-body')

            # Step 3.B: Load more articles if necessary
            if isinstance(card['maxPrice'], Decimal):
                load_more_articles(session, funct_result, soup, card, articles_table)

            # Step 4: Iterate over articles
            for article_row in articles_table.children:
                # Step 4.A: Check if this is a proper article
                if 'article-row' not in article_row.attrs['class']:
                    funct_result.addWarning('No offers found for card ("{}") with parameters: {} {}.'.format(card['title'], params, card['maxPrice']))
                    break

                # Step 4.B: Check if the user can purchase the item, ship to is address available from the seller.
                action_container = article_row.find('div', class_='actions-container')
                if not action_container.find('div', class_='input-group'):
                    # Cannot purchase, skip this article_row
                    continue

                # Step 4.C: Retrieve Seller info
                seller_name_tag = article_row.find('span', class_='seller-name').find('a')
                seller_name = seller_name_tag.contents[0]

                seller_sales_info_wrapper = article_row.find('span', class_='seller-extended').contents[1]
                seller_sales_number = re.match(r'^\d+', seller_sales_info_wrapper['title']).group(0)

                # Step 4.D Skip if we already added an article (of this card) for this seller
                if seller_name in card_sellers_names:
                    # Skip this article_row
                    continue

                seller_profile_url = CARDMARKET_BASE_URL + seller_name_tag['href']

                price_str = article_row.find('div', class_='price-container').find('span', class_='text-right').contents[0]
                price = Decimal(price_str.split(' ')[0].replace('.','').replace(',','.'))
                # Step 4.E: Check if price isn't above maxPrice
                if isinstance(card['maxPrice'], Decimal) and price > card['maxPrice']:
                    # The current article price is superior than the max price
                    # we stop iterate over article (article are listed according to price)
                    break

                # Step 4.F: Create the new article
                article_attributes = article_row.find('div', class_='product-attributes')
                article_condition = article_attributes.a.span.contents[0]
                article_language = article_attributes.find('span', class_='icon')['data-original-title']

                article_dict = { 'name': card['title'], 'url': card_full_url, 'language': article_language, 'condition': article_condition, 'price': price }

                # Step 4.G: Handle seller comment for the article
                if articles_comment:
                    article_comment = ""
                    article_comment_wrapper = article_row.find('div', class_='product-comments')
                    if article_comment_wrapper:
                        article_comment = article_comment_wrapper.find('span', class_='text-truncate').contents[0]

                    article_dict['comment'] = article_comment

                # Step 4.H: Add this article on the seller key in the dict
                if seller_name in sellers:
                    sellers[seller_name]['cards'].append(article_dict)
                else:
                    sellers[seller_name] = {'url': seller_profile_url, 'sales': seller_sales_number, 'cards': [ article_dict ] }

                # Step 4.I: Add seller name in the corresponding list
                card_sellers_names.append(seller_name)

    return funct_result

def determine_relevant_sellers(sellers, max_sellers):
    LOG.debug('------- The Wizard is sorting sellers to find relevant ones...')

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
    funct_result = FunctResult()

    """Delete a file"""

    if path_file and path_file.exists():
        try:
            if path_file.is_file():
                LOG.debug('  |____ Deleting the previous result page...')
                import os
                os.remove(path_file)
        except Exception as e:
            funct_result.addError('Failed to delete "{}". Reason: {}'.format(path_file, e))
            return funct_result
    return funct_result

def build_result_page(wantlists_info, max_sellers, sellers, relevant_sellers):
    funct_result = FunctResult()
    LOG.debug('------- The Wizard is creating a beautiful result page...')

    # Step 1: Retrieve content of template.html
    soup = None
    template_path = Path.cwd().joinpath('assets', 'template.html')
    try:
        with open(template_path, 'r', encoding='utf-8') as template_file:
            template_contents = template_file.read()
            soup = BeautifulSoup(template_contents, 'html.parser')
    except IOError as err:
        funct_result.addError('Template file "{}" cannot be properly opened.'.format(template_path))
        funct_result.addError(err)
        return funct_result

    # Step 2: Edit the template
    # Step 2.A: Add "max_sellers" value
    max_sellers_parent_tag = soup.find('span', id='max-sellers-value')
    max_sellers_parent_tag.string = str(max_sellers)

    # Step 2.B: Add wantlists
    wantlists_parent_tag = soup.find('div', id='wantlist-links')
    wantlists_links_html_str = ''
    for wantlist_info in wantlists_info:
        wantlists_links_html_str += '<a class="wantlist-item button" href="{}" target="_blank" rel="noopener noreferrer">{}</a>'.format(wantlist_info[0], wantlist_info[1])
    wantlists_parent_tag.append(BeautifulSoup(wantlists_links_html_str, 'html.parser'))

    # Step 2.C: Retrieve containers tags and declare variables for relevant sellers
    sellers_parent_tag = soup.find('div', id='relevant-sellers-items')
    sellers_html_str = ''

    sellers_cards_lists_parent_tag = soup.find('div', id='sellers-cards-lists')
    sellers_cards_lists_html_str = ''

    # Step 2.D: Create HTML contents for relevant sellers
    seller_index = 0
    for relevant_seller in relevant_sellers:
        index_5_digits_str = '{:05}'.format(seller_index)
        sellers_html_str += '<div class="seller-item"><a href="{}" id="seller-{}" class="seller-name" target="_blank" rel="noopener noreferrer">{}</a><span id="seller-{}-sales-number" class="hidden">{}</span><hr><span class="number-cards">Cards: <b>{}</b></span><span class="total-price">Total: {} €</span><a href="#" onclick="showCardsList(\'{}\'); return false;" class="link-cards-list button">See Cards ></a></div>'.format(sellers[relevant_seller[0]]['url'], index_5_digits_str, relevant_seller[0], index_5_digits_str, sellers[relevant_seller[0]]['sales'], str(relevant_seller[1]), str(relevant_seller[2]), index_5_digits_str)
        # Concatenate cards list
        sellers_cards_lists_html_str += '<div id="seller-{}-cards" class="cards-list">'.format(index_5_digits_str)

        for card in sellers[relevant_seller[0]]['cards']:
            article_comment = ""
            if 'comment' in card:
                article_comment = card['comment']
            sellers_cards_lists_html_str += '<div class="card-item"><span class="card-condition {}">{}</span><span class="card-language {}"></span><a href="{}" class="card-title" target="_blank" rel="noopener noreferrer">{}</a><span class="card-comment" title="{}">{}</span><span class="card-price">{} €</span></div>'.format(card['condition'], card['condition'], card['language'], card['url'], card['name'], article_comment, article_comment, card['price'])
        sellers_cards_lists_html_str += '</div>'

        seller_index += 1

    # Step 2.E: Append HTML for relevant sellers
    sellers_parent_tag.append(BeautifulSoup(sellers_html_str, 'html.parser'))
    sellers_cards_lists_parent_tag.append(BeautifulSoup(sellers_cards_lists_html_str, 'html.parser'))

    # Step 3: Save as "result.html" in current project directory
    result_path = Path.cwd().joinpath('result.html')

    # Step 3.A: if "result.html" exists delete it
    delete_result = delete_previous_result_page(result_path)
    funct_result.append(delete_result)
    if not delete_result.isValid():
        return funct_result

    LOG.debug('  |____ Saving the result page...\n')

    # Step 3.B: Create and write to the file
    try:
        with open(result_path, 'w+', encoding='utf-8') as result_file:
            result_file.write(str(soup))
    except IOError as err:
        funct_result.addError('Error while creating the result file ("{}").'.format(result_path))
        funct_result.addError(err)
        return funct_result

    LOG.info('The result page has been created here: "{}"\n'.format(result_path.as_uri()))

    # Step 4: Open the result page
    import webbrowser
    try:
        webbrowser.open(result_path.as_uri())
    except webbrowser.Error:
        # Since it's not critical at all only display a warning.
        funct_result.addWarning('Failed to automatically open the result page for you.')

    funct_result.addResult(result_path.as_uri())

    return funct_result

def cardmarket_wantlist_wizard(credentials, wantlist_urls, continue_on_warning, max_sellers, articles_comment=False):
    funct_result = FunctResult()
    LOG.debug('------- Calling the Wizard...\r\n')

    end_intro_message = 'these whislists urls!' if len(wantlist_urls) > 1 else 'this wantlist url!'
    LOG.info('Hi there... You are here to find great card deals, right? Humm... okay... Give me {}'.format(end_intro_message))
    LOG.warning('Be aware that he\'s very old and can be sometimes grumpy and slow to perform all these tasks.\r\n')

    # Step 1: Create a web session (to be able to stay connected)
    with requests.Session() as session:
        # Step 2: Log-in to Cardmarket
        funct_result = cardmarket_log_in(session, credentials)
        funct_result.logMessages()
        if not funct_result.isValid():
            # FATAL error we cannot perform anything without being log-in
            return False

        sellers = {}
        wantlists_info = []
        LOG.debug('------- Handling the wantlist(s)')
        for wantlist_url in wantlist_urls:
            # Step 2: Retrieve wantlist in JSON
            retrieve_result = retrieve_wantlist(session, wantlist_url, continue_on_warning)
            retrieve_result.logMessages()
            funct_result.append(retrieve_result)
            if retrieve_result.isWarning():
                # Empty wantlist, or unable to retrieve wantlist but continue_on_warning is True
                continue
            elif not retrieve_result.isValid():
                # Only break, not return so we can still log out of Cardmarket
                break

            wantlist = retrieve_result.getResult()

            # Step 2.A: Add info to the wantlists_info list
            wantlists_info.append((wantlist_url, wantlist.pop(0)))

            # Step 3: Populate the sellers dictionary
            populate_result = populate_sellers_dict(session, sellers, wantlist, continue_on_warning=continue_on_warning, articles_comment=articles_comment)
            populate_result.logMessages()

            funct_result.append(populate_result)

        # Step 4: Display most relevant sellers
        if funct_result.isValid() or (funct_result.isWarning() and continue_on_warning):
            relevant_sellers = determine_relevant_sellers(sellers, max_sellers)

            if relevant_sellers:
                build_result = build_result_page(wantlists_info, max_sellers, sellers, relevant_sellers)
                build_result.logMessages()

                funct_result.append(build_result)
                result_path = build_result.getResult()
                if result_path != None:
                    funct_result.setResult(result_path)

        # Step 5: Logout from Cardmarket, simply a safety mesure.
        logout_result = cardmarket_log_out(session)
        logout_result.logMessages()

        funct_result.append(logout_result)

    # Avoid issue(s) by ensuring we have a result
    if funct_result.getResult() == None:
        funct_result.addResult('')

    return funct_result

def get_credentials_from_file():
    funct_result = FunctResult()

    LOG.debug('------- Retrieving credentials...')

    credentials = None

    # Step 1: Check if the path point to an existing file
    if not CREDENTIALS_PATH.exists():
        # File not found
        funct_result.addWarning('file \'credentials.json\' doesn\'t exists in the current directory.')
        return funct_result

    # Step 2: Open the file as JSON
    try:
        with open(CREDENTIALS_PATH, 'r', encoding='utf-8') as json_file:
            credentials = json.load(json_file)
    except json.JSONDecodeError as err:
        funct_result.addError('Issue(s) in the JSON file: {} (line {} pos {}).'.format(err.msg, err.lineno, err.pos))
        return funct_result
    except IOError as err:
        funct_result.addError('Credentials file "{}" cannot be properly opened.'.format(CREDENTIALS_PATH))
        funct_result.addError(err)
        return funct_result

    # Step 3: Check if the JSON object contains the necessary keys and values
    #         And the values are strings
    keys_to_check = ['login', 'password']
    for key in keys_to_check:
        if key not in credentials:
            funct_result.addError('Key "{}" not present in the credentials JSON file "{}".'.format(key, CREDENTIALS_PATH))
            return funct_result
        if not credentials[key] or not isinstance(credentials[key], str):
            funct_result.addError('Value of key "{}" isn\'t of type string in the credentials JSON file "{}".'.format(key, CREDENTIALS_PATH))
            return funct_result

    funct_result.addResult(credentials)
    return funct_result

def check_wantlists_and_max_sellers(wantlist_urls, max_sellers, silently=False):
    funct_result = FunctResult()

    if not silently:
        LOG.debug('------- Checking inputs parameters...')

    # Declare variables to store values that will be at the end set to GLOBAL variables
    global_language = None
    global_game = None

    # Step 1: Check the wantlist urls
    for wantlist_url in wantlist_urls:
        if not isinstance(wantlist_url, str):
            funct_result.addError('wantlist url need to be of type string.')
            continue
        matched = re.match(CARDMARKET_BASE_URL_REGEX + r'\/(\w{2})\/(\w+)\/Wants\/\d+$', wantlist_url)
        if not matched:
            funct_result.addError('Invalid wantlist url ("{}"), valid pattern is:'.format(wantlist_url))
            funct_result.addError(CARDMARKET_BASE_URL + '/<LANGUAGE_CODE>/<GAME_NAME>/Wants/<wantlist_CODE>')
            continue
        if not global_game:
            (global_language, global_game) = matched.groups()
    if not funct_result.isValid():
        return funct_result

    # Step 2: Check value of "max_sellers"
    if max_sellers < 0:
        funct_result.addError('Input parameter "max_sellers" need to be an int superior to 0.')
        return funct_result
    elif max_sellers == 0 or max_sellers > 300:
        funct_result.addWarning('Value of input parameter "max_sellers" is set to "{}", caution this means the process can be long and the result page can be heavy.'.format(max_sellers))

    # Step 3: Check validity of global info
    if not global_language or len(global_language) != 2 or not global_language.islower():
        funct_result.addError('The language code in one of the wantlist url isn\'t formated correctly, need to be 2 character long, only lowercase.')
        return funct_result
    # Since new games can be added to Cardmarket, checking "global_game" is not worth it

    # Step 4: Assign info to global variables
    global CURR_LANG
    global CURR_GAME
    CURR_LANG = global_language
    CURR_GAME = global_game

    return funct_result

def create_credentials_file(credentials, silently=False):
    # Normaly we write to file only if we checked the credentials so :
    # Step 1: Add a special key to skip checking the credentials in the future
    credentials['skip-check'] = 'YES'

    # Step 2: Create the JSON file and dump credentials
    with open(CREDENTIALS_PATH, 'w+', encoding='utf-8') as json_file:
        json.dump(credentials, json_file, indent=4, ensure_ascii=False)

    if not silently:
        LOG.debug('Credentials file successfully created ("{}")'.format(CREDENTIALS_PATH))

    return True

def check_credentials_validity(credentials, silently=False):
    funct_result = FunctResult()

     # Step 1: Create a web session
    with requests.Session() as session:
        # Step 2: Log-in to Cardmarket
        funct_result = cardmarket_log_in(session, credentials, silently=silently)
        if not funct_result.isValid():
            return funct_result

        logout_result = cardmarket_log_out(session, silently=silently)
        funct_result.append(logout_result)

    # This will update the file and add the 'skip-check' property
    create_credentials_file(credentials, silently=True)

    funct_result.addResult(credentials)
    return funct_result
