import os, json
from cprint import cprint, cconvert
from get_params_web import get_parameters


def get_params(ignore_list:list, settings:dict) -> dict:
    # Get computer name
    username = os.getlogin()
    # Get VRC OSC directory
    directory = settings['directory'].replace("&USER&", username)

    if not os.path.isdir(directory):
        cprint(f"\n\n[R]Directory: [Y]{directory} [R]Was not found.")
        cprint("\n[R][!] [Y]Did you change the directory in the settings?")
        cprint("[R][!] [Y]Did you enable OSC In Vrchat?\n\n")
        cprint("Follow the setup for this program here: [U][B]https://github.com/JessaTehCrow/VRC_control#how-to-install")
        input(cconvert("\n[G]Press enter to exit"))
        exit()

    # Load saved avatars
    with open("avatars.json","r") as f:
        avatar_data = json.load(f)

    users = os.listdir(directory)

    avatars = []
    # Find and load all avatars
    for user in users:
        dir = directory + user + "/Avatars"

        for avatar in os.listdir(dir):
            with open(dir+f"/{avatar}", "r") as f:
                data = json.loads(f.read()[3:])
                cprint("[GR]Avatar found:[E] "+ dir+f"/{avatar}")
                avatars.append(data)

    cprint("\n\n[GR]Loaded avatars:")
    for i,x in enumerate(avatars):
        cprint(f"[E]  {i}  -  [Y]{x['name']}")
    
    avatar = avatars[0]
    if len(avatars) > 1:
        avatar = avatars[int(input(cconvert("[G]Select avatar: [E]")))]

    cprint(f"\n[G]Selected avatar: [E]{avatar['name']}")

    # Get parameters and ignore from ignore list (Base vrchat params)
    parameters = []
    for i,parameter in enumerate(avatar['parameters']):
        # If parameter in ignore list, 
        if parameter['name'] in ignore_list or not 'input' in parameter: continue
        # Save parameter
        parameters.append([parameter['name'], parameter['input']['type']])

    # User filtered ignore
    new_ignore = []
    loaded_save = False

    if avatar['name'] in avatar_data:
        cprint("[GR]Avatar save detected.")
        inp = input(cconvert("[E]Load save? [G](y/n)[E]: "))

        if inp.lower() in ['y','ye','yes']:
            new_ignore = avatar_data[avatar['name']]
            loaded_save = True

        elif inp.lower() not in ['n','no']:
            cprint("[R]Enter Y or N")
            exit()

    if not loaded_save:
        # Get user custom ignore list from web-input
        # Format:
        # [save_to_disk:bool, *parameter_to_ignore:string]
        #
        new_ignore = get_parameters(parameters, settings['port'])
        save = new_ignore.pop(0)
        cprint("[GR][INFO] [E]Received data")

        if save:
            with open("avatars.json",'w') as f:
                avatar_data[avatar['name']] = new_ignore
                json.dump(avatar_data, f, indent=4)

    data = {}
    # Prepare final parameter data for database
    for param in parameters:
        if param[0] in new_ignore:
            continue

        data[param[0]] = {
            "type"  : param[1],
            "value" : 0,
            "locked": 0
        }

    return data