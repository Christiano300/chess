from math import sqrt


# Nur Vornamen ausgeben
namen = ["Marko Brajkovic",  # = ["Marko", "Brajkovic"]
         "Christian Patzl", "Jonas Böhmwalder"]
# for i in namen:
#     liste = i.split()
#     print(liste[0])


for i in namen:
    liste = i.split()
    liste.reverse()
    print(" ".join(liste))  # *liste


def ziffsum(zahl: int) -> int:

    summe = 0
    for i in str(zahl):
        summe += int(i)
    return summe


liste = [2, 6, 2, 7, 4, 8]
#        0, 1, 2, 3, 4, 5

for i in range(len(liste)):  # 0, 1, 2, 3, 4, 5
    print(liste[i])

for i in liste:  # 2, 6, 2, 7, 4, 8
    print(i)


def is_prim(zahl: int) -> bool:
    if zahl >= 1:
        for i in range(2, round(sqrt(zahl))):
            if not zahl % i:
                return False
    return True


l = [2, 5, 8, 3, 9, 11, 20]
lp = []

for i in l:
    if is_prim(i):
        lp.append(i)

# print(lp)


liste = [4, 1]


def f():
    liste.append(8)
    print("Lokal:", liste)


print("Global:", liste)
f()
print("Global:", liste)


a = "Hallo"  # ["Hallo"]
liste = [a, 3, "Hi"]
print(liste)


lst1 = [1, 2, 3, 4, 5, 6]
lst2 = [1, 2, 3, 4, 5, 6][:]

lst1.append([7, 8, 9])
lst2.extend([7, 8, 9])

print(lst1)
print(lst2)

print(len(lst1))
print(len(lst2))



liste = [1, 2, 3, 4, 5, 6, 2, 1, 4, 8]
print(liste)
del liste[1]
print(liste)
liste.remove(1)
print(liste)
a = liste.pop(1)
print(liste)
print(a)


liste = [1, 2, 3, 4, 5, 6, 1, 1, 4, 8]

i = 0
while i < len(liste):
    if liste[i] == 1:
        del liste[i]
    else:
        i += 1

while True:
    if 1 in liste:
        liste.remove(1)
    else:
        break

print(liste)


liste = [5, 6, 7, 8, 9, 10, 11, 12, 13]
print(sum(liste))
print(min(liste))
print(max(liste))


def ziffsum(zahl: int) -> int:
    return sum([int(i) for i in str(zahl)])


print(ziffsum(96432187))


# Riesenhuber Gerd

def flip_name(name):
    a = name.split()
    a.reverse()
    return " ".join(a)



def flip_name(name):
    name.reverse()
    return " ".join(name)

testname = ["Gerd", "Riesenhuber"]
# Riesenhuber Gerd

print(flip_name(testname))


string = "Gerd.Riesenhuber"
a = string.split(".")
print(a)


liste = [4, 1, 2, 3, 4, 5, 6, 7, 8]
liste[0], liste[-1] = liste[-1], liste[0]




def betrag(zahl):
    if zahl < 0:
        return zahl * -1
    return zahl	

def posi(zahl):
    if zahl < 0:
        return -1
    elif zahl == 0:
        return 0
    return 1

zahl = int(input("Zahl: "))
print("Betrag:", betrag(zahl))
print("Posi:", posi(zahl))


def clean_str(s):
    a = ""
    for i in s:
        if i.isalpha() or i.isspace():
            a += i
    return a
    return "".join([i for i in s if i.isalpha() or i.isspace()])
    a = []
    for i in s:
        if i.isalpha() or i.isspace():
            a.append(i)
    return "".join(a)

txt = "I§ch %b&i/n (wie%der§ ei!n :T&ex,t!" 


def teile_ort(s):
    plz = int(s[-4:])
    ort = s[:-5]
    return ort, plz
    

l = ["St. Pölten 3100", "Krems 3500", "Wien 1200", "Linz 4020"]
#nl = [("St. Pölten", 3100), ("Krems", 3500), ("Wien", 1200), ("Linz", 4020)]

for i in range(len(l)):
    l[i] = teile_ort(l[i])

print(l)