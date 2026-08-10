import pymem
import re


PM = None
module_addr_cache = {}
process_name = "hl.exe"


"""
FOV获取候选
"PlayerFOVGetter": "client.dll + 0x12755C"
"PlayerFOVGetter": "client.dll + 0x1275B0"
"""
cheat_table = {
    "PlayerHealth": "[hw.dll + 0x100CC60] + 0x504",
    "PlayerPosGetter": "[hw.dll + 0x100CC60] + 0x504 - 0x158",
    "PlayerAngGetter": "[hw.dll + 0x100CC60] + 0x504 - 0xEC",
    "PlayerFOVGetter": "client.dll + 0x10A4B4",
    "RobotListHealthAddr": "[hw.dll + 0x100CC60] + 0x504",
    "EntitySize": 0x324,
    "HealthPosOffset": -0x158,
    "HealthAngOffset": -0xEC,
}

def find_pm():
    global PM
    try:
        PM = pymem.Pymem(process_name)
    except (pymem.exception.CouldNotOpenProcess, pymem.exception.ProcessNotFound):
        print(process_name + " 未找到")
        module_addr_cache.clear()
        PM = None

def read_addr(addr: int) -> int | None:
    if PM is None:
        raise ValueError("PM 为 None")
    return PM.read_uint(addr)

def get_module_addr(module_name: str) -> int | None:
    if PM is None:
        module_addr_cache.clear()
        raise ValueError("PM 为 None")

    if module_name in module_addr_cache:
        return module_addr_cache[module_name]

    module = pymem.process.module_from_name(PM.process_handle, module_name)
    if module is None:
        raise ValueError("Module not found")
    else:
        module_addr_cache[module_name] = module.lpBaseOfDll
        return module.lpBaseOfDll


def get_addr_by_key(key: str) -> int | None:
    global cheat_table

    if PM is None:
        return None

    addrStr = cheat_table.get(key, None)
    if addrStr is None:
        return None
    
    source = addrStr.replace("[", "read_addr(")
    source = source.replace("]", ")")
    source = re.sub(r"([^\s<>\"'\[\]\(\)]+)\.(dll|exe)", r"get_module_addr('\1.\2')", source)

    try:
        source = eval(source, {
            "read_addr": read_addr,
            "get_module_addr": get_module_addr,
        })
    except (ValueError, pymem.exception.ProcessError, pymem.exception.MemoryReadError) as e:
        print(f"获取地址失败, 代码: {source}, PM: {PM}, 错误信息: {e}")
        return None

    return source


def read_vector(addr: int) -> tuple[float, float, float] | None:
    return (
        PM.read_float(addr + 0x0),
        PM.read_float(addr + 0x4),
        PM.read_float(addr + 0x8),
    )

def write_vector(addr: int, vec: tuple[float, float, float]) -> None:
    PM.write_float(addr + 0x0, vec[0])
    PM.write_float(addr + 0x4, vec[1])
    PM.write_float(addr + 0x8, vec[2])


class Player:
    def __init__(self):
        raise TypeError("此类无法实例化")

    @staticmethod
    def get_pos() -> tuple[float, float, float] | None:
        plyPosAddr = get_addr_by_key("PlayerPosGetter")
        if plyPosAddr is not None:
            return read_vector(plyPosAddr)
        else:
            return None

    @staticmethod
    def get_ang() -> tuple[float, float, float] | None:
        plyAngAddr = get_addr_by_key("PlayerAngGetter")
        if plyAngAddr is not None:
            return read_vector(plyAngAddr)
        else:
            return None

    @staticmethod
    def get_fov() -> float | None:
        plyFOVAddr = get_addr_by_key("PlayerFOVGetter")
        if plyFOVAddr is not None:
            return PM.read_float(plyFOVAddr)
        else:
            return None

class RobotList:
    def __init__(self):
        raise TypeError("此类无法实例化")

    @staticmethod
    def get_health(robotIdx: int) -> float | None:
        robotListHealthAddr = get_addr_by_key("RobotListHealthAddr")
        if robotListHealthAddr is not None:
            return PM.read_float(robotListHealthAddr + robotIdx * cheat_table["EntitySize"])
        else:
            return None

    @staticmethod
    def get_pos(robotIdx: int) -> tuple[float, float, float] | None:
        robotPosAddr = get_addr_by_key("RobotListHealthAddr")
        if robotPosAddr is not None:
            return read_vector(robotPosAddr + robotIdx * cheat_table["EntitySize"] + cheat_table["HealthPosOffset"])
        else:
            return None

    @staticmethod
    def get_ang(robotIdx: int) -> tuple[float, float, float] | None:
        robotAngAddr = get_addr_by_key("RobotListHealthAddr")
        if robotAngAddr is not None:
            return read_vector(robotAngAddr + robotIdx * cheat_table["EntitySize"] + cheat_table["HealthAngOffset"])
        else:
            return None


if __name__ == "__main__":
    import time

    while True:
        time.sleep(1) 
        find_pm()
        if PM is not None:
            break

    while True:
        time.sleep(1)

        pos = Player.get_pos()
        ang = Player.get_ang()
        print("玩家位置:", pos)
        print("玩家角度:", ang)

        for robotIdx in range(10):
            health = RobotList.get_health(robotIdx)
            pos = RobotList.get_pos(robotIdx)
            ang = RobotList.get_ang(robotIdx)
            print(f"机器人 {robotIdx} 健康值: {health}, 位置: {pos}, 角度: {ang}")

