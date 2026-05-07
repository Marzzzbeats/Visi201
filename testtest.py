import dis

def f():
    i = 0
    while i < 5 :
        i+=1
    return True

print(dis.dis(f))