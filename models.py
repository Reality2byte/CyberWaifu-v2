"""
conversation.py
Provides packages for model operating
"""


import tools
import types
import chatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory
from google.generativeai import configure as gemini_configure
import google.generativeai as genai
import google.genai
import torch
import whisper
import config
import time
import os
import logger
import webFrontend.config

from google_login import load_creds


# whisper model is no longer needed
# mps is not available for whisper
# interfereDevice = 'cuda' if torch.cuda.is_available() else 'cpu'
# audioModel = whisper.load_model(
#     'medium', torch.device(interfereDevice), in_memory=True)


def initialize():
    if config.AUTHENTICATE_METHOD == 'oauth':
        os.environ.pop('GOOGLE_API_KEY')
        gemini_configure(credentials=load_creds(), api_key=None)
        logger.Logger.log('Authenticated Google OAuth 2 session.')
        logger.Logger.log('Available base models:', [
            m.name for m in genai.list_tuned_models()])
        logger.Logger.log('My tuned models:', [m.name for m in genai.list_tuned_models()])


# No need to handle by users, so not in config.py
MODEL_SAFETY_SETTING = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}


# google did not provide the fucking interface for counting token.
# well, now I get it
def TokenCounter(string: str) -> int:
    return ChatGoogleGenerativeAI(model=config.USE_MODEL).get_num_tokens(string)


def PreprocessPrompt(originalPrompt: str, tVars):
    for i in tVars:
        originalPrompt = originalPrompt.replace('{{' + i + '}}', tVars[i])
    return originalPrompt


def BaseModelProvider(temperature:float = 0.9) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=config.USE_LEGACY_MODEL,
        convert_system_message_to_human=True,
        temperature=temperature,
        safety_settings=MODEL_SAFETY_SETTING,
    )
    


def ChatModelProvider(system_prompt: str, enabled_plugins: list[dict]) -> chatModel.ChatGoogleGenerativeAI:
    return chatModel.ChatGoogleGenerativeAI(
        model=config.USE_MODEL,
        temperature=0.7,
        safety_settings=MODEL_SAFETY_SETTING,
        system_prompt=system_prompt,
        tools=enabled_plugins,
    )


def MemorySummarizingModel(charName: str, pastMemories: str) -> AIMessage:
    llm = ChatGoogleGenerativeAI(
        model=config.USE_MODEL_IMAGE_PARSING,
        convert_system_message_to_human=True,
        temperature=0.9,
        safety_settings=MODEL_SAFETY_SETTING,
        credentials=load_creds() if config.AUTHENTICATE_METHOD == 'oauth' else None)

    preprocessed = PreprocessPrompt(
        config.MEMORY_MERGING_PROMPT,
        {
            'charName': charName,
            'pastMemories': pastMemories
        }
    )
    return llm.invoke([
        HumanMessage(content=preprocessed)
    ])


def ImageParsingModelProvider():
    return ChatGoogleGenerativeAI(
        model=config.USE_MODEL_IMAGE_PARSING, convert_system_message_to_human=True, temperature=1, safety_settings=MODEL_SAFETY_SETTING, credentials=load_creds() if config.AUTHENTICATE_METHOD == 'oauth' else None)


def ImageParsingModel(image: str) -> str:
    logger.Logger.log(image)
    llm = ImageParsingModelProvider()
    return llm.invoke([
        HumanMessage(
            ["You are received a image, your task is to descibe this image and output text prompt",
             {"type": "image_url", "image_url": f'http://{webFrontend.config.APP_HOST}:{webFrontend.config.APP_PORT}/api/v1/attachment/{image}'}]
        )
    ]).content


def EmojiToStickerInstrctionModel(text: str, availableStickers: list[str]) -> str:
    p = PreprocessPrompt(config.TEXT_EMOJI_TO_INSTRUCTION_MAPPING_PROMPT, {
        'message': text,
        'availableStickers': availableStickers
    })
    return BaseModelProvider(1).invoke([HumanMessage(p)]).content


def AudioToTextModel(audioPath: str) -> str:
    # result = audioModel.transcribe(audioPath)
    # return result['text']
    return "" # deprecated
