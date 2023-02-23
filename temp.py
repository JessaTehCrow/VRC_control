from cprint import cprint,cconvert

avis = [
    "crow",
    "bird-avatar",
    "birbred"
]

cprint(f"\n\n\n\n[GR]Loaded avatars:")
[cprint(f"[E]{i}  -  [Y]{x}") for i,x in enumerate(avis)]
input(cconvert("[G]Select avatar:[E] "))