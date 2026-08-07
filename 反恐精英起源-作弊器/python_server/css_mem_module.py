"""
"BotInfoListAddr": "[client.dll + 0x69CD30] + 0x60",
"BotInfoSize": 0x140,
"TeamTypeOffset": 0,
"HealthPosOffset": 0x4,
"PosOffset": 0x8,
"AngOffset": 0x14,
"FOVGetter": "client.dll + 0x68D078"
"""
import sysmemtool as MemTool



HANDLE = None
PROCESS_NAME = "cstrike_win64.exe"
PID = None
MODULE_ADDR = {}

OFFSET = {
    "BotInfoSize": 0x140,
    "TeamTypeOffset": 0,
    "HealthOffset": 0x4,
    "PosOffset": 0x8,
    "AngOffset": 0x14,
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
   
        temp = MemTool.readUInt64(HANDLE, PID, clientDllAddr + 0x69CD30)
        if temp is None:
            return None
        result = {}
        botInfoListAddr = temp + 0x60 + botIdx * OFFSET["BotInfoSize"]

        teamType = MemTool.readUInt32(HANDLE, PID, botInfoListAddr + OFFSET["TeamTypeOffset"])
        if teamType is None:
            return None

        # 0: 未知 1: 观察者 2: 恐怖分子 3: 警察
        if teamType > 3:
            return None

        result["TeamType"] = BotInfo.TeamTypeMapping[teamType]
        result["Health"] = MemTool.readUInt32(HANDLE, PID, botInfoListAddr + OFFSET["HealthOffset"])
        result["Pos"] = MemTool.readFloatVector(HANDLE, PID, botInfoListAddr + OFFSET["PosOffset"])
        result["Ang"] = MemTool.readFloatVector(HANDLE, PID, botInfoListAddr + OFFSET["AngOffset"])
        return result


class PlayerInfo:
    def __init__(self):
        raise TypeError("此类无法实例化")

    def getData() -> dict | None:
        data = BotInfo.getData(0)
        if data is None:
            return None
        
        clientDllAddr = MODULE_ADDR["client.dll"]
        data["FOV"] = MemTool.readUInt32(HANDLE, PID, clientDllAddr + 0x68D078)
        return data



if __name__ == "__main__":
    import time
    Init()
    while True:
        time.sleep(1)

        playerInfo = PlayerInfo.getData()
        print(playerInfo)
  
  

