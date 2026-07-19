-- ========== 配置 ==========
local newValue = 9999.0              -- 你要设置的固定数值
local batchSize = 1000              -- 每次处理的地址数量，根据实际情况调整
-- ========== 配置 ==========

local list = getAddressList()
if list == nil then
    print("没有地址列表")
    return
end

local count = math.min(list.Count, batchSize)

print(string.format("共处理 %d 个地址", count))

for i = 0, count - 1 do
    local rec = list[i]
    if rec then rec.Value = newValue end
end

