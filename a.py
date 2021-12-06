def move(x, nums):
    return [n for n in nums if n != x]+[n for n in nums if n == x]

print(move(0, [int(n) for n in input().split(' ')]))
