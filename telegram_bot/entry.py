import os
import yaml
import telegram

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot.util import build_menu, states_map
from telegram_bot.ocr_functions import run_scraper

STATES_YAML = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'states.yaml')
with open(STATES_YAML, 'r') as stream:
  try:
    states_all = yaml.safe_load(stream)
  except yaml.YAMLError as exc:
    print(exc)

SENTINEL = dict()

def entry(bot, update):

    # Is this a reply to something?
    if update.callback_query:
        # if this is a reply to the `/start` message, it should contain a state code
        if update.callback_query.message.reply_to_message.text == '/start':
            state_code = update.callback_query.data.lower()
            SENTINEL['state_code'] = state_code

            # TODO - check what type of input is required for this state (from yaml file)
            url_type = states_all[state_code]['type']

            if url_type == 'html':
                # run directly
                run_scraper(bot, update.callback_query.message.chat.id, SENTINEL['state_code'], url_type, states_all[state_code]['url'])
            else:
                # reply back asking for file
                bot.send_message(
                    chat_id=update.callback_query.message.reply_to_message.chat.id,
                    text=f"Upload {states_all[state_code]['type']} for {state_code}"
                )

    # Is this a direct message?
    if update.message:

        # If the direct message is `/start`
        if update.message.text and update.message.text.startswith("/start"):
            button_list = []
            for st_name in states_map.keys():
                button_list.append(
                    InlineKeyboardButton(
                        st_name, callback_data=states_map[st_name]
                    )
                )
            reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))
            bot.send_message(
                chat_id=update.message.chat.id,
                text="Which state do you want to fetch data for?",
                reply_to_message_id=update.message.message_id,
                reply_markup=reply_markup,
            )
            return

        # If the direct message is `/test`
        elif update.message.text and update.message.text.startswith("/test"):
            update.message.reply_text("200 OK!", parse_mode=telegram.ParseMode.MARKDOWN)
            return

        # If the direct message is `/help`
        elif update.message.text and update.message.text.startswith("/help"):
            help_text = f"""
            \n*OCR*
            - Send the bulletin image to do OCR
            - Errors and the results would be returned
            - If there are errors, copy the extracted text and make corrections.
            - Send it back to the text
            - Reply to the message with `/ocr2 "Madhya Pradesh"`
            \n*PDF*
            - Send the URL of the pdf bulletin
            - Choose the state. Default page number is 2.
            - For using different page number, use the command like below
            - `/pdf "Punjab" 3`
            \n*DASHBOARD*
            - `/dashboard`
            - Choose the state
            \n\n_Send `/test` for checking if the bot is online_"""

            update.message.reply_text(
                str(help_text), parse_mode=telegram.ParseMode.MARKDOWN
            )
            return

        # If the direct message is file type of PDF
        elif update.message.document and update.message.document.mime_type == 'application/pdf':
            pdf_path = '/tmp/{}.pdf'.format(SENTINEL['state_code'].lower())
            pdf_file = update.message.document.get_file()
            pdf_file.download(pdf_path)
            run_scraper(bot, update.message.chat.id, SENTINEL['state_code'], 'pdf', pdf_path)

        # If the direct message is file type of image
        elif update.message.photo:
            print('this is a photo for', SENTINEL)
            photo = update.message.photo[-1]
            image_path = '/tmp/{}.jpg'.format(SENTINEL['state_code'].lower())
            image_file = bot.get_file(photo.file_id)
            image_file.download()

            # rename file name to <datetime stamp_state_code>
            # pass the path to run_scraper
            run_scraper(bot, update.message.chat.id, SENTINEL['state_code'], 'image', image_path)

        else:
            print('this is something else complletely')