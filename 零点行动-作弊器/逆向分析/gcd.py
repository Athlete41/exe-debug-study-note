import math
from functools import reduce

addresses = ["15950AA8", "15954330", "159489E4"]

nums = sorted(int(addr, 16) for addr in addresses)
diffs = [nums[j] - nums[i] for i in range(len(nums)) for j in range(i+1, len(nums))]


print(diffs)

if diffs:
    gcd_val = reduce(math.gcd, diffs)
    print(f"\n最大公约数: 0x{gcd_val:X} ({gcd_val})")
    
    # 列出最大公约数的所有正因数
    factors = []
    for i in range(1, int(gcd_val**0.5) + 1):
        if gcd_val % i == 0:
            factors.append(i)
            if i != gcd_val // i:
                factors.append(gcd_val // i)
    factors.sort()
    
    print("\n所有公因数（十进制）:")
    for factor in factors:
        print(factor, hex(factor))
else:
    print("地址少于2个，无法计算差值和公约数。")


"""

"""