import css_mem_module



class CSSCheatMainWindow:
    FPS = 30.0
    BOT_MAX = 32

    SLIENT = False

    def __init__(self):
        css_mem_module.Init()


    def timerTask(self):
        try:
            data = []
            for i in range(self.BOT_MAX):
                botInfo = css_mem_module.BotInfo.getData(i)
                botTeamType = botInfo["TeamType"]

                if botTeamType is None or botTeamType not in self.BOT_FILTER:
                    continue 

                data.append(botInfo)
    
        except Exception as e:
            if not self.SLIENT:
                print(e)





