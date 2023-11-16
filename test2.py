def myround(x, prec=2, base=.05):
    return round(base * round(float(x)/base),prec)

print(myround(1.3409248, base=0.025))