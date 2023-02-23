import os,re
os.system("")

class color:
    BL = '\u001b[30m' #black
    G = '\033[90m' #gray
    L = '\033[96m' #light blue
    P = '\033[95m' #purple
    B = '\033[94m' #blue
    GR = '\033[92m' #green
    Y = '\033[93m' #yellow
    R = '\033[91m' #red
    E = '\033[0m\x1b[0m' #clear
    BO = '\033[1m' #bold
    U = '\033[4m'  #underline
    EBG = '\x1b[6;0;0m' #clear bg
    RBG = '\x1b[6;41m' #red bg
    GRBG = '\x1b[6;42m' #green bg
    YBG = '\x1b[6;43m' #yellow bg
    BBG = '\x1b[6;44m' #blue bg
    PBG = '\x1b[6;45m' #purple bg
    LBG = '\x1b[6;46m' #light blue bg
    WBG = '\x1b[6;47m' #White bg
    GBG = '\x1b[1;7;30m' #gray bg
    ERR = '\x1b[6;39;41m' #error

colors = {}

#i made most of this like 2 years ago, no judge pls
for x in color.__dict__:
    if not x.endswith("_"):
        exec(f"colors['[{x}]'] = color.{x}")

def cconvert(sentence:str):
    for x in colors:
        sentence = sentence.replace(x,colors[x])
        sentence = sentence.replace(f"\\{colors[x]}", x)
        sentence = sentence.replace(f"\\{x}", f"\\\\{colors[x]}")
    return sentence

def cprint(*sentence):
    sentence = cconvert(' '.join(sentence))

    print(sentence + colors["[E]"])
