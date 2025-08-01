"""
memory.py
@biref Provides a interface to access and interact with multi-character's memories.    
"""

import os
import json
import config
import logger
import models
import dataProvider
import tools


class Memory:
    """
    @biref Provides a interface to access and interact with multi-character's memories.
    """

    def __init__(self, dProvider: dataProvider.DataProvider, char: str, rtSession: bool = False):
        # create if not exist
        self.dataProvider = dProvider
        self.rtSession = rtSession
        # read character messages
        logger.Logger.log(char, self.dataProvider.getCharacterId(char), '114514')
        self.char = self.dataProvider.getCharacter(
            self.dataProvider.getCharacterId(char))

    def getExampleChats(self) -> str:
        return self.char['exampleChats']

    def getCharName(self) -> str:
        return self.char['charName']

    def getPastMemories(self) -> str:
        return self.char['pastMemories']

    def getCharPrompt(self) -> str:
        return self.char['charPrompt']
    
    def getCharTTSServiceId(self) -> int:
        return self.char['ttsServiceId']
    
    def getCharTTSUseModel(self) -> str:
        return self.char['AIDubUseModel']
    

    def getAvailableStickers(self) -> list[dict[str, str | int]]:
        return self.dataProvider.getStickerList(self.char['emotionPack'])

    def storeCharPrompt(self, prompt: str) -> None:
        self.char['charPrompt'] = prompt
        self.save()
        
    def getCharStickerSet(self) -> int:
        return self.char['emotionPack']
    
    def getCharExampleChats(self) -> int:
        return self.char['exampleChats']
    
    def getCharTHA4Service(self) -> int:
        return self.char['tha4Service']

    def save(self) -> None:
        self.dataProvider.updateCharacter(self.dataProvider.getCharacterId(
            self.getCharName()), self.getCharName(), self.getCharTTSUseModel(), self.getCharStickerSet(), self.getCharPrompt(), self.getPastMemories(), exampleChats=self.getExampleChats(), tha4Service=self.getCharTHA4Service())

    def storeMemory(self, userName: str, conversation: str) -> None:
        self.char['pastMemories'] = self.char['pastMemories'].strip() + \
            '\n' + conversation
        if models.TokenCounter(self.char['pastMemories']) > config.MEMORY_SUMMARIZING_LIMIT:
            self.char['pastMemories'] = models.MemorySummarizingModel(
                self.getCharName(), self.char['pastMemories']).content
        self.save()

    def createCharPromptFromCharacter(self, userName):
        if self.rtSession:
            return models.PreprocessPrompt(config.VOICE_CHAT_INITIAL_PROMPT, {
                'charName': self.getCharName(),
                'userName': userName,
                'datePrompt': tools.TimeProvider(),
                'charPrompt': self.getCharPrompt(),
                'memoryPrompt': self.getPastMemories(),
                'exampleChats': self.getExampleChats(),
                'availableEmotions': ', '.join(self.dataProvider.getAvailableTTSReferenceAudio(self.getCharTTSServiceId())),
                'userPersona': self.dataProvider.getUserPersona(),
                'toolsPrompt': config.TOOLS_PROMPT
            })
        else:
            availableStickers = ''
            for i in self.getAvailableStickers():
                availableStickers += f'({i['name']}), '
            availableStickers = availableStickers[0: -2]
            return models.PreprocessPrompt(config.INITIAL_PROMPT, {
                'charName': self.getCharName(),
                'userName': userName,
                'datePrompt': tools.TimeProvider(),
                'charPrompt': self.getCharPrompt(),
                'memoryPrompt': self.getPastMemories(),
                'exampleChats': self.getExampleChats(),
                'availableStickers': availableStickers,
                'userPersona': self.dataProvider.getUserPersona(),
                'toolsPrompt': config.TOOLS_PROMPT
            })
