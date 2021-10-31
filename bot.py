import logging
import os
from urllib import parse
import pyshorteners
import sys

import requests
from flask import Flask, request

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, update
from telegram.chataction import ChatAction
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler,Filters, CallbackQueryHandler, InlineQueryHandler, ConversationHandler

from googlesearch import search

# Instanciar acortador de url
shorter = pyshorteners.Shortener()

# Configuracion Loggin
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Estados de la conversacion
MODO, SEARCH, GETURL, MENU = range(4)

# Funciones para responder a los handlers
def start(update: Update, context: CallbackContext):
    logger.info(f'Usuario: {update.effective_user.first_name}, con id: {update.message.chat_id} ha iniciado en el bot')
    update.message.reply_text(
        text=f'<i>Hola! {update.effective_user.first_name}, con este <b>bot</b> podra buscar en la web cualquier tipo de contenido. Al igual puede utilizarlo para acortar URls.</i>',
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([['Buscar en la Web 🔎'], ['Acortar URL ✂️']],resize_keyboard=True, one_time_keyboard=True)
    )
    return MODO

def menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer('Menu')
    
    query.edit_message_text(
    text=f'<i>Hola! {update.effective_user.first_name}, con este <b>bot</b> podra buscar en la web cualquier tipo de contenido. Al igual puede utilizarlo para acortar URls.</i>',
    parse_mode="HTML",
    reply_markup=ReplyKeyboardMarkup([['Buscar en la Web 🔎'], ['Acortar URL ✂️']],resize_keyboard=True, one_time_keyboard=True)
    )
    return MODO

def to_url(update: Update, context: CallbackContext):
    update.message.reply_text(
        text='<i>Envienos el url a acortar</i>',
        parse_mode='HTML' 
    )
    return GETURL

def get_url(update: Update, context: CallbackContext):
    url = update.message.text
    url_short = shorter.clckru.short(url)
    update.message.reply_text(
        text=f'<i>La url acortada es </i>\n <b>{url_short}</b>',
        parse_mode='HTML'
    )
            
    update.message.reply_text(
        text='<i>Pulse </i> /start <i>para volver al menu principal</i>',
        parse_mode='HTML'
    )
    return ConversationHandler.END
    

def ask_type(update: Update, context: CallbackContext):
    update.message.reply_text(
        text='<i>Antes de enviarme lo que desea buscar. Digame que tipo de busqueda desea hacer</i>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(
            [ ['Simple', 'Medio', 'Intenso'] ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return MODO

modo = ''
def ask_for_mode(update: Update, context: CallbackContext): 
    m = update.message.text
    global modo 
    modo = m
    update.message.reply_text(
        text=f'<i>Haremos una busqueda {m}, por faor envie lo que desea buscar </i>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    return SEARCH

def show_results(update: Update, context: CallbackContext):
    question = update.message.text
       
    if modo == 'Simple':
        results = search(question, num=3, start=0, stop=3, pause=2.0)
    elif modo == 'Medio':
        results = search(question, num=5, start=0, stop=5, pause=2.0)
    elif modo == 'Intenso':
        results = search(question, num=7, start=0, stop=7, pause=2.0)
        
    update.message.reply_text(
        text='<i>Los resultados mas interesantes en la web sobre <b> "{}" </b> son:</i>'.format(question.upper()),
        parse_mode='HTML'
        )


    for url in results:
        to_url = shorter.clckru.short(url)
        update.message.reply_text(
            text=f"<a>{to_url}</a>\n",
            parse_mode='HTML'
        )
        
    update.message.reply_text(
        text='<i>Pulse </i> /start <i>para volver al menu principal</i>',
        parse_mode='HTML'
    )
    return ConversationHandler.END


def fallback(update: Update, context: CallbackContext):
    update.message.reply_text(
        text='Disculpa, no te he entendido'
    )
    return MODO

def main():
    # Obtener Token
    TOKEN = os.getenv('TOKEN')
    mode = os.getenv('MODE')
                  
    app = Flask(__name__)      
    app.route('/', methods=['POST'])  
        
    # Eligiendo el modo      
    if mode == 'dev':
        # Modo de desarrollo
        def run(updater):
            # Start Bot
            updater.start_polling()
            # Cerrar co Ctrl+C
            updater.idle()
    elif mode == 'prod':
        # WEBHOOKS
        def run(updater):
            PORT = int(os.environ.get("PORT", "5000"))
            app.run(host='0.0.0.0', port=PORT, debug=True)
    else:
        logger.info('No se especifico el MODE')      
        sys.exit()
        
    # Creo el UPDATER
    updater = Updater(TOKEN)
    
    # Creo el dispatcher
    dispatcher = updater.dispatcher
    
    search_conversation = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
                      ],
        states={
            MODO: [
                MessageHandler(Filters.regex('^Buscar en la Web 🔎$'), ask_type),
                MessageHandler(Filters.regex('^Acortar URL ✂️$'), to_url),
                MessageHandler(Filters.regex('^Simple|Medio|Intenso$'), ask_for_mode)
                ],
            GETURL: [MessageHandler(Filters.entity('url'), get_url)],
            SEARCH: [MessageHandler(Filters.text, show_results)]
        },
        fallbacks=[]
    )
    
    # Agrego los Hadlers
    dispatcher.add_handler(search_conversation)

    run(updater)

if __name__=='__main__':
    main()