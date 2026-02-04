from dis import *

def test_affectation():
    a = 10
    return a

print(dis(test_affectation))

def test_if():
    a = 10
    if a == 10 :
        res = True
    else :
        res = False
    return res

print(dis(test_if))
