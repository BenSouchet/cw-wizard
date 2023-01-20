import threading
import queue

import tkinter
import tkinter.font
import tkinter.scrolledtext

from functools import partial

from core import SCRIPT_NAME, VERSION, MAXIMUM_SELLERS
from core import create_credentials_file
from core import get_credentials_from_file
from core import check_credentials_validity
from core import check_wantlists_and_max_sellers
from core import cardmarket_wantlist_wizard

THREAD_QUEUE = queue.Queue()

GUI_WINDOW_WIDTH = 600
GUI_WINDOW_HEIGHT = 300

GUI_ENTRY_BORDER_WIDTH = 2
GUI_ENTRY_BORDER_CLR = '#645c53'

GUI_FONT_LIST = ['Trebuchet MS', 'Helvetica', 'Lucida Sans', 'Tahoma', 'Arial']

GUI_FONT_STYLES = {}

class guiWindow:
  def __init__(self):
    self.root = tkinter.Tk()
    self.width = GUI_WINDOW_WIDTH
    self.height = GUI_WINDOW_HEIGHT
    self.main_bg_color = '#24201d'
    self.content_bg_color = '#1a1816'
    self.title = tkinter.StringVar()
    self.description = tkinter.StringVar()
    self.description_label = None
    self.content = None
    self.button_abort_text = 'ABORT'
    self.button_next_text = tkinter.StringVar()
    self.button_next = None
    self.step = ''
    self.credentials = None

def center_window(window):
    # Always do an update of the idle tasks to get the most acurate size & position values
    window.root.update_idletasks()

    # Normaly equal to window.width and window.height
    width = window.root.winfo_reqwidth()
    height = window.root.winfo_reqheight()

    frm_width = window.root.winfo_rootx() - window.root.winfo_x()
    win_width = width + 2 * frm_width

    titlebar_height = window.root.winfo_rooty() - window.root.winfo_y()
    win_height = height + titlebar_height + frm_width

    # Compute the position
    x = window.root.winfo_screenwidth() // 2 - win_width // 2
    y = window.root.winfo_screenheight() // 2 - win_height // 2

    # Update size and position of the window
    window.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    # if the window is minimized restore it
    window.root.deiconify()

def create_label(parent, text, font_style, bg_color):
    label = tkinter.Label(parent, font=GUI_FONT_STYLES[font_style]['font'], background=bg_color, foreground=GUI_FONT_STYLES[font_style]['font-color'])
    if isinstance(text, tkinter.StringVar):
        label.configure(textvariable=text)
    else:
        label.configure(text=text)
    return label

def create_button(parent, text, bg_color):
    button = tkinter.Button(parent, font=GUI_FONT_STYLES['button']['font'], background=GUI_FONT_STYLES['button']['background-color'], highlightbackground=bg_color, foreground=GUI_FONT_STYLES['button']['font-color'], disabledforeground=GUI_FONT_STYLES['button']['disabled-font-color'])
    if isinstance(text, tkinter.StringVar):
        button.configure(textvariable=text)
    else:
        button.configure(text=text)
    return button

def validate_entry_is_integer(new_value):
    if str.isdigit(new_value) or new_value == '':
        return True
    return False

def create_entry(parent, variable, bg_color, password=False, width=0, int_only=False):
    entry = tkinter.Entry(parent, textvariable=variable, background=bg_color, foreground=GUI_FONT_STYLES['content']['font-color'], insertbackground=GUI_FONT_STYLES['content']['font-color'], highlightcolor=GUI_ENTRY_BORDER_CLR, highlightbackground=GUI_ENTRY_BORDER_CLR, highlightthickness=GUI_ENTRY_BORDER_WIDTH)
    if password:
        entry.configure(show='*')
    if width != 0:
        entry.configure(width=width)

    if int_only:
        entry.configure(validate='all')
        vcmd = (parent.register(validate_entry_is_integer))
        entry.configure(validatecommand=(vcmd, '%P'))

    return entry

def create_text_area(parent, bg_color):
    return tkinter.scrolledtext.ScrolledText(parent, background=bg_color, highlightcolor=GUI_ENTRY_BORDER_CLR, highlightbackground=GUI_ENTRY_BORDER_CLR)

def _populate_font_styles():
    global GUI_FONT_STYLES
    global GUI_FONT_LIST

    # Step 1: Retrieve font curently available in the machine
    available_fonts = tkinter.font.families()

    # Step 2: As a fallback take the most safe font we listed
    font_name = GUI_FONT_LIST.pop()

    # Step 3: Check if a "better" font is available
    for curr_font_name in GUI_FONT_LIST:
        if curr_font_name in available_fonts:
            # We found a better font
            font_name = curr_font_name
            break

    # Step 4: Create font styles
    GUI_FONT_STYLES['title'] = { 'font': (font_name, 22, tkinter.font.BOLD), 'font-color': '#FFFFFF' }
    GUI_FONT_STYLES['description'] = { 'font': (font_name, 12), 'font-color': '#aaaaaa' }
    GUI_FONT_STYLES['content'] = { 'font': (font_name, 12), 'font-color': '#FFFFFF' }
    GUI_FONT_STYLES['button'] = { 'font': (font_name, 12), 'font-color': '#24201d', 'disabled-font-color': '#4a4542', 'background-color': '#feffff' }

def close_window(window):
    window.root.destroy()

def wizard_wrapper(credentials, wantlist_urls, max_sellers):
    # Step 1: Call the Wizard
    result = cardmarket_wantlist_wizard(credentials, wantlist_urls, continue_on_warning=True, max_sellers=max_sellers)
    result.logMessages()

    # Step 2: Push result into the thread queue
    global THREAD_QUEUE
    THREAD_QUEUE.put(result)

def credentials_validity_wrapper(credentials):
    # Step 1: Check the validity
    result = check_credentials_validity(credentials, silently=True)
    result.logMessages()

    # Step 2: If valid create the file to avoid the user to enter them again
    if result.isValid():
        create_credentials_file(credentials)

    # Step 3: Push result into the thread queue
    global THREAD_QUEUE
    THREAD_QUEUE.put(result)

def wizard_has_finished(params):
    # Step 1: Check if the thread as finished
    if params[1].is_alive():
        # Not yet, wait and run again
        params[0].root.after(200, wizard_has_finished, params)
        return False

    # Step 2: Retrieve the result
    result = THREAD_QUEUE.get()

    # Step 3: Display the final screen
    window_operation_over(params[0], result)

    return True

def credentials_validity_has_finished(params):
    # Step 1: Check if the thread as finished
    if params[1].is_alive():
        # Not yet, wait and run again
        params[0].root.after(200, credentials_validity_has_finished, params)
        return False

    # Step 2: Retrieve the result from the thread queue
    result = THREAD_QUEUE.get()

    if not result.isValid():
        # Couldn't connect, display error message
        window_request_credentials(params[0], '\n'.join(result.getMessages(message_type='error')))
        return False

    # Step 3: Store credentials dict in the window object
    params[0].credentials = result.getResult()

    # Step 4: Now we need to request wantlist(s) from the user
    window_request_wantlists(params[0])

    return True

def next_step(window, param1, param2):
    if window.step == 'request_credentials':
        # Step 1: Create a credentials dict
        credentials = { 'login': param1.get(), 'password': param2.get() }

        # Step 2: Check validity

        # Step 2.A: Quick credentials check
        if not credentials['login'] or not credentials['password']:
            set_window_description(window, 'Error: field(s) cannot be empty.', is_error=True)
            return True

        # Step 2.B: Cardmarket connexion test in a thread
        window_wait_screen(window)
        thread = threading.Thread(target=credentials_validity_wrapper, args=(credentials,), daemon=True)
        thread.start()

        # Step 4: Callback to display the final screen when the wizard has finished
        window.root.after(200, credentials_validity_has_finished, (window, thread))
    elif window.step == 'request_wantlists':
        # Step 1: Convert parameters
        wantlist_urls = param1.get("1.0", tkinter.END).splitlines()
        # Step 1.A: remove empty lines
        if not wantlist_urls:
            wantlist_urls = list(filter(None, wantlist_urls))
        # Step 1.B: Get max_sellers as int
        max_sellers = int(param2.get())

        # Step 2: Check validity

        # Step 2.A: Quick check
        if not wantlist_urls:
            set_window_description(window, 'Error: you need to specify at least one wantlist URL.', is_error=True)
            return True

        # Step 2.B: Full check
        result = check_wantlists_and_max_sellers(wantlist_urls, max_sellers, silently=True)
        result.logMessages()
        if not result.isValid():
            set_window_description(window, 'Error: At least one URL is invalid, check your terminal for the details.', is_error=True)
            return True

        # Step 3: All seems good, display the waiting screen and call the wizard !
        window.step = 'wizard_in_progress'
        window_wait_screen(window)
        thread = threading.Thread(target=wizard_wrapper, args=(window.credentials, wantlist_urls, max_sellers,), daemon=True)
        thread.start()

        # Step 4: Callback to display the final screen when the wizard has finished
        window.root.after(200, wizard_has_finished, (window, thread))
    else:
        close_window(window)

    return True

def create_default_widgets(window):
    # Step 1: Create the title label, it will display the current step title
    label_title = create_label(window.root, window.title, 'title', window.main_bg_color)
    label_title.grid(column=0, row=0, pady=(14, 5), sticky=tkinter.N)

    # Step 2: Create the description label, will show description of current step
    window.description_label = create_label(window.root, window.description, 'description', window.main_bg_color)
    window.description_label.grid(column=0, row=1, pady=(5, 14), sticky=tkinter.N)

    # Step 3: Create the content frame, will store widgets used for current step
    window.content = tkinter.Frame(window.root, background=window.content_bg_color)
    window.content.grid(column=0, row=3, sticky=tkinter.NSEW)
    window.content.grid_columnconfigure(0, weight=1)
    window.content.grid_rowconfigure(0, weight=1)

    # Step 4: Create frame and buttons Abort et Next
    frame_buttons = tkinter.Frame(window.root, background=window.main_bg_color)
    frame_buttons.grid(column=0, row=4, padx=14, pady=14, sticky=tkinter.NSEW)
    frame_buttons.grid_columnconfigure(0, weight=1)
    frame_buttons.grid_rowconfigure(0, weight=1)

    window.button_abort = create_button(frame_buttons, window.button_abort_text, window.main_bg_color)
    window.button_abort.configure(command=partial(close_window, window))
    window.button_abort.grid(column=0, row=0, sticky=tkinter.NW)

    window.button_next = create_button(frame_buttons, window.button_next_text, window.main_bg_color)
    window.button_next.grid(column=1, row=0, sticky=tkinter.NE)

def set_window_description(window, message, is_error=False, is_warn=False):
    if is_error:
        window.description_label.configure(foreground='red')
    elif is_warn:
        window.description_label.configure(foreground='yellow')
    else:
        window.description_label.configure(foreground=GUI_FONT_STYLES['description']['font-color'])

    window.description.set(message)

def window_request_credentials(window, error_msg=None):
    # Step 1: Set current prog step
    window.step = 'request_credentials'

    # Step 2: Set title and description
    window.title.set('Enter your Cardmarket credentials:')
    if error_msg:
        set_window_description(window, error_msg, is_error=True)
    else:
        set_window_description(window, 'Required to access your Cardmarket wantlists.')

    # Step 3: Create credentials widgets

    # Step 3.A: Clear the window content frame
    for child_widget in window.content.winfo_children():
        child_widget.destroy()

    # Step 3.B: Start by creating the parent frame for the credential widgets.
    frame_credentials = tkinter.Frame(window.content, background=window.content_bg_color)
    frame_credentials.grid(column=0, row=0)
    frame_credentials.grid_columnconfigure(1, weight=1)

    # Step 3.C: Create the variables that will store the credentials
    username = tkinter.StringVar()
    password = tkinter.StringVar()

    # Step 3.D: Create the two rows: username & password
    label_username = create_label(frame_credentials, 'Username', 'content', window.content_bg_color)
    label_username.grid(row=0, column=0, pady=(0, 4), sticky=tkinter.E)
    entry_username = create_entry(frame_credentials, username, window.content_bg_color)
    entry_username.grid(row=0, column=1, ipadx=4, padx=(4, 0), pady=(0, 4), sticky=tkinter.NSEW)

    label_password = create_label(frame_credentials, 'Password', 'content', window.content_bg_color)
    label_password.grid(row=1, column=0, sticky=tkinter.E)
    entry_password = create_entry(frame_credentials, password, window.content_bg_color, password=True)
    entry_password.grid(row=1, column=1, padx=(4, 0), sticky=tkinter.NSEW)

    # Step 4: Add disclaimer message
    text_disclaimer = 'Disclaimer: If you have 2FA activate on your account this script won\'t work.'
    label_disclaimer = create_label(window.content, text_disclaimer, 'description', window.content_bg_color)
    label_disclaimer.grid(row=1, column=0, pady=(0, 14), sticky=tkinter.S)

    # Step 5: Force a visual update to "fix" invisible widgets (tkinter.Entry elems wasn't rendered)
    window.root.update()
    window.root.update_idletasks()

    # Step 6: Update Next button
    window.button_next_text.set('NEXT STEP')
    window.button_next.configure(state=tkinter.NORMAL)
    window.button_next.configure(command=partial(next_step, window, username, password))

def window_request_wantlists(window):
    # Step 1: Set current prog step
    window.step = 'request_wantlists'

    # Step 2: Set title and description
    window.title.set('Enter the wantlist(s) URL(s):')
    set_window_description(window, 'One URL per line (starting with "https://")')

    # Step 3: Create wantlists widgets

    # Step 3.A: Clear the window content frame
    for child_widget in window.content.winfo_children():
        child_widget.destroy()

    # Step 3.B: Start by creating the parent frame for the credential widgets.
    frame_wantlists = tkinter.Frame(window.content, background=window.content_bg_color)
    frame_wantlists.grid(column=0, row=0, padx=12, pady=(3, 6))
    frame_wantlists.grid_columnconfigure(0, weight=1)
    frame_wantlists.grid_rowconfigure(1, weight=1)

    # Step 3.C: Create the text area
    label_username = create_label(frame_wantlists, 'Wantlist(s):', 'content', window.content_bg_color)
    label_username.grid(row=0, column=0, pady=(0, 4), sticky=tkinter.W)
    wantlists_area = create_text_area(frame_wantlists, window.content_bg_color)
    wantlists_area.grid(row=1, column=0, sticky=tkinter.NSEW)

    # Step 4: Now create the max sellers frame, label and entry
    max_sellers = tkinter.StringVar()
    max_sellers.set(MAXIMUM_SELLERS)
    frame_max_sellers = tkinter.Frame(window.content, background=window.content_bg_color)
    frame_max_sellers.grid(row=1, column=0, padx=12, pady=(0, 10), sticky=tkinter.EW)
    label_max_sellers = create_label(frame_max_sellers, 'Max Sellers', 'content', window.content_bg_color)
    label_max_sellers.grid(row=0, column=0, sticky=tkinter.E)
    entry_max_sellers = create_entry(frame_max_sellers, max_sellers, window.content_bg_color, width=5, int_only=True)
    entry_max_sellers.grid(row=0, column=1, sticky=tkinter.NSEW)
    label_max_sellers = create_label(frame_max_sellers, 'Default value 20. 0 means display all.', 'description', window.content_bg_color)
    label_max_sellers.grid(row=0, column=2, padx=(10, 0), sticky=tkinter.E)

    # Step 5: Force a visual update to "fix" invisible widgets (tkinter.Entry elems wasn't rendered)
    window.root.update()
    window.root.update_idletasks()

    # Step 6: Update Next button
    window.button_next_text.set('START')
    window.button_next.configure(state=tkinter.NORMAL)
    window.button_next.configure(command=partial(next_step, window, wantlists_area, max_sellers))

def window_operation_over(window, result):
    # Step 1: Set current prog step
    window.step = 'operation_over'

    # Step 2: Detroy / clean the content frame
    for child_widget in window.content.winfo_children():
        child_widget.destroy()

    # Step 3: Create a label inside the content frame
    content_msg = tkinter.StringVar()
    content_label = create_label(window.content, content_msg, 'description', window.content_bg_color)
    content_label.configure(wraplength=472)

    # Step 4: Set texts according to the current step
    window.title.set('The Wizard has finished!')

    result_uri = result.getResult()
    no_error_msg = 'Normally a webpage as open in your default browser with the results.\nIf not open the file "{}".\n\nHave a wonderful day!'.format(result_uri)
    if result.isValid():
        set_window_description(window, 'All tasks ended successfully.')
        content_msg.set(no_error_msg)
    elif result.isWarning():
        set_window_description(window, 'Warning(s) occured, check your terminal for the details.', is_warn=True)
        content_msg.set(no_error_msg)
    else:
        # This means there was error(s)
        set_window_description(window, 'Error(s) occured, check your terminal for more details.')
        content_msg.set('\n'.join(result.getMessages(message_type='error')))

    # Step 5: Now the text is set properly place the label
    content_label.grid(row=0, column=0)

    # Step 6: Force a visual update
    window.root.update()
    window.root.update_idletasks()

    # Step 7: Update next button text
    window.button_next_text.set('CLOSE')
    window.button_next.configure(state=tkinter.NORMAL)

def window_wait_screen(window):
    # Step 1: Detroy / clean the content frame
    for child_widget in window.content.winfo_children():
        child_widget.destroy()

    # Step 2: Create a label inside the content frame
    content_msg = tkinter.StringVar()
    content_label = create_label(window.content, content_msg, 'description', window.content_bg_color)
    content_label.configure(wraplength=472)

    # Step 3: Set texts according to the current step
    set_window_description(window, 'Please wait for the process to finish.')
    if window.step == 'request_credentials':
        window.title.set('Checking credentials...')
        content_msg.set('The program check if we can estasblish a connection to Cardmarket using your credentials, this can takes up to 1 minute.')
    elif window.step == 'wizard_in_progress':
        window.title.set('The Wizard looks for the best deals...')
        content_msg.set('This operation can takes time according to the total number of items in the wishlists and the maximum number of sellers you requested to see.')

    # Step 4: Now the text is set properly place the label
    content_label.grid(row=0, column=0)

    # Step 5: Force a visual update
    window.root.update()
    window.root.update_idletasks()

    # Step 6: Update ext button text and disable it
    window.button_next_text.set('IN PROGRESS...')
    window.button_next.configure(state=tkinter.DISABLED)

def set_window_icon(window):
    # I tested a bunch of code with ICO, ICNS, PNG, GIF, XBM  without success to get a generic way to handle all platforms
    from platform import system
    system_platform = system()

    if system_platform == 'Windows':
        # Method that's only work on Windows and cause blank title bar icon on Mac OS
        window.root.iconbitmap(default='assets/images/icon.ico')
    else:
        # Dont know if this method work on Linux but it's the only working one for Mac OS
        icon = tkinter.PhotoImage(file='assets/images/icon.png')
        window.root.iconphoto(True, icon)

def create_window():
    # Step 1: Create the window obj
    window = guiWindow()

    # Step 2: Set icon
    set_window_icon(window)

    # Step 3: Before doing anything we make the window fully transparent
    window.root.attributes('-alpha', 0.0)

    # Step 4: Create the font styles we will use in the interface
    _populate_font_styles()

    # Step 5: Set title
    window.root.title("{} - version {}".format(SCRIPT_NAME, VERSION))

    # Step 6: Set dimensions
    window.root.configure(width=window.width, height=window.height)
    window.root.grid_columnconfigure(0, weight=1)
    window.root.grid_rowconfigure(3, weight=1)

    # Step 7: Disable resize + full screen mode
    window.root.resizable(False, False)

    # Step 8: Set background color
    window.root.configure(background=window.main_bg_color)

    # Step 9: Center the window in the screen
    center_window(window)

    # Step 10: Create default elements and place them into the root
    create_default_widgets(window)

    return window

def main():
    """Entry point of the CW Wizard GUI script"""

    # Step 1: Initialize and create the window
    window = create_window()

    # Step 2: Retrieve credentials and check validity
    result = get_credentials_from_file()
    result.logMessages()

    if result.isValid():
        # Check the credentials are valid
        credentials = result.getResult()
        if 'skip-check' not in credentials:
            result = check_credentials_validity(credentials, silently=True)
            result.logMessages()
        # Since we have maybe check the validity second check to the result
        if result.isValid():
            window.credentials = result.getResult()

    # Step 3: Set the appropriate first step on the window
    if not window.credentials:
        window_request_credentials(window)
    else:
        window_request_wantlists(window)

    # Step 4: Put back the alpha of the window to full opaque
    window.root.attributes('-alpha', 1.0)

    # Step 5: Start the window mainloop
    window.root.mainloop()

    return True

if __name__ == '__main__':
    main()
