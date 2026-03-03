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

def semaine_lente():
    secondes_par_jour = 86400
    return secondes_par_jour * 7 

def semaine_rapide():
    return 86400*7

# print(dis(semaine_lente))
# print(dis(semaine_rapide))

def afficheA():
    print("a")
    return None

print(dis(afficheA))