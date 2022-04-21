liste = [2, 3]


def f():
    liste.extend([4])
    print("Lokal:", liste)


print("Global:", liste)
f()
print("Global:", liste)
