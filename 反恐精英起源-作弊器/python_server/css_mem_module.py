"""
"BotInfoListAddr": "[client.dll + 0x69CD30] + 0x40",
"BotInfoSize": 0x140,
"NameOffset": 0x0,
"TeamTypeOffset": 0x20,
"HealthPosOffset": 0x24,
"PosOffset": 0x28,
"AngOffset": 0x34,
"FOVGetter": "client.dll + 0x68D078"
"""
import sysmemtool as MemTool



HANDLE = None
PROCESS_NAME = "cstrike_win64.exe"
PID = None
MODULE_ADDR = {}

OFFSET = {
    "BotInfoSize": 0x140,
    "NameOffset": 0x0,
    "TeamTypeOffset": 0x20,
    "HealthOffset": 0x24,
    "PosOffset": 0x28,
    "AngOffset": 0x34,
}

def Init():
    global HANDLE, PID, MODULE_ADDR

    HANDLE = MemTool.openDevice()
    status, PID = MemTool.getPidByName(HANDLE, PROCESS_NAME)
    if status == 0 and PID == 0:
        raise Exception(f"[-] 获取 PID 失败，进程名 {PROCESS_NAME}, 状态 {status}, 返回值 {PID}")

    status, clientDllAddr = MemTool.getModuleBase(HANDLE, PID, "client.dll")
    if status != 0:
        raise Exception(f"[-] 获取模块基址失败，模块名 \"client.dll\", 状态 {status}, 返回值 {clientDllAddr}")
    MODULE_ADDR["client.dll"] = clientDllAddr


class BotInfo:
    TeamTypeMapping = [
        "未知",
        "观察者",
        "恐怖分子",
        "警察",
    ]


    def __init__(self):
        raise TypeError("此类无法实例化")

    @staticmethod
    def getData(botIdx: int) -> dict | None:
        clientDllAddr = MODULE_ADDR["client.dll"]
   
        botInfoListAddr = MemTool.readUInt64(HANDLE, PID, clientDllAddr + 0x69CD30)
        if botInfoListAddr is None:
            return None
        else:
            botInfoListAddr += 0x40

        result = {}
        botInfoAddr = botInfoListAddr + botIdx * OFFSET["BotInfoSize"]
        name = MemTool.readString(HANDLE, PID, botInfoAddr + OFFSET["NameOffset"], 0x20, encoding='utf-8') 
        if name is None:
            return None
        
        teamType = MemTool.readUInt32(HANDLE, PID, botInfoAddr + OFFSET["TeamTypeOffset"])
        if teamType is None:
            return None

        # 0: 未知 1: 观察者 2: 恐怖分子 3: 警察
        if teamType > 3:
            return None
        
        result["Name"] = name # 转换为字符串并解码为 UTF-8
        result["TeamType"] = BotInfo.TeamTypeMapping[teamType]
        result["Health"] = MemTool.readUInt32(HANDLE, PID, botInfoAddr + OFFSET["HealthOffset"])
        result["Pos"] = MemTool.readFloatVector(HANDLE, PID, botInfoAddr + OFFSET["PosOffset"])
        result["Ang"] = MemTool.readFloatVector(HANDLE, PID, botInfoAddr + OFFSET["AngOffset"])
        return result


class FOVGetter:
    def __init__(self):
        raise TypeError("此类无法实例化")

    def getData() -> int | None:
        clientDllAddr = MODULE_ADDR["client.dll"]
        return MemTool.readUInt32(HANDLE, PID, clientDllAddr + 0x68D078)



if __name__ == "__main__":
    import time
    Init()
    while True:
        time.sleep(1)
        print(BotInfo.getData(0))
  
  

