-- 需要满足基本假设才可以使用: Vector 是三个连续的 float 并且以 x 为基地址

local camPosBaseAddr = "client.dll + E0388"
local camAngBaseAddr = "client.dll + E0394"

local entitiesPosAddrList = {

}

local entitiesPosNameList = {

}

-- for i = 2, 30 do
--     table.insert(entitiesPosAddrList, string.format("1650AA30 + 324 * %d + D0", i))
-- end

function findAddrByName(list, name)
    if list == nil then
        print("没有地址列表")
        return
    end

    local targetAddrList = {}
    for i = list.Count - 1, 0, -1 do
        local rec = list[i]
        if rec and rec.Description then
            if rec.Description == name then
                return rec.Address
            end
        end
    end

    return nil
end






local filePath = "G:\\project\\exe-debug-study-note\\C3DGAME\\render_data.json"
local interval_ms = 100
local json = require("json")

function getVectorByAddr(addr)
    if type(addr) == "string" then
        addr = getAddress(addr)
    end
    if not addr then return nil, nil, nil end
    return readFloat(addr), readFloat(addr + 4), readFloat(addr + 8)
end

function loopCall()
    local px, py, pz = getVectorByAddr(camPosBaseAddr)
    local ap, ay, ar = getVectorByAddr(camAngBaseAddr)

    local data = {
        camera = {
            pos = { px, py, pz },
            ang = { ap, ay, ar },
            fov = nil
        },
        entities = {
            
        }
    }

    for _, addr in ipairs(entitiesPosAddrList) do
        local px, py, pz = getVectorByAddr(addr)
        table.insert(data.entities, {
            id = addr,
            name = addr,
            pos = { px, py, pz },
            ang = { }
        })
    end

    local list = getAddressList()
    for _, name in ipairs(entitiesPosNameList) do
        local addr = findAddrByName(list, name)
        if addr ~= nil then
            local px, py, pz = getVectorByAddr(addr)
            table.insert(data.entities, {
                id = string.format("%s-%s", addr, name),
                name = name,
                pos = { px, py, pz },
                ang = { }
            })
        end
    end

    local jsonStr = json.encode(data)
    local file = io.open(filePath, "w")

    if file then
        file:write(jsonStr)
        file:close()
    end
end


timer = createTimer()
timer.Interval = interval_ms
timer.OnTimer = loopCall
timer.Enabled = true


print("Render 数据写入已启动，文件: " .. filePath)
print("要停止，在 Lua 窗口执行: timer.Enabled = false")