

#FAIT EN PARTIE PAR L'IA

import dis


it: int = 4


def add(x, y):
    return x + y

print("Avant exécution :")
dis.dis(add, adaptive=True, show_caches=True)

for i in range(it):
    add("a", "b")

print("\nAprès beaucoup d'appels avec str :")
dis.dis(add, adaptive=True, show_caches=True)


for i in range(it):
    add(i, i)

print("\nAprès beaucoup d'appels avec int :")
dis.dis(add, adaptive=True, show_caches=True)
