-- ========== 配置 ==========
local targetDescription = "Vec-"   -- 修改这里：要删除的描述关键词（部分匹配即可）
-- ========== 配置结束 ==========

local list = getAddressList()
if list == nil then
    print("没有地址列表")
    return
end

local count = list.Count

for i = count - 1, 0, -1 do
    local rec = list[i]
    if rec and rec.Description then
        if string.find(rec.Description, targetDescription) then
            rec.delete()
        end
    end
end

