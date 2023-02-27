# VRC_control

Control your avatar's parameters through a web-application

- [Features](#features)
- [How to install](#how-to-install)
    - [Program](#executable-only)
    - [Cloning](#repo-clone)
- [How to use](#how-to-use)
- [Sharing control](#sharing-control-with-other-people)
    - [Port forwarding](#port-forwarding)
    - [Ngrok](#ngrok-program)
- [Settings](#Settings)
    - [Web port](#web-port)
    - [OSC directory](#osc-directory)
- [Known problems](#known-problems)
- [TODO](#todo)


## Features

- ***EVERY*** sdk3 avatar is compatible
- Lock toggles and sliders
- Set avatar toggles from your browser
- Share across the internet

*Examples:*

https://user-images.githubusercontent.com/29403110/221006121-2cdabd1f-5e5d-4e82-b9d2-073616d3303d.mp4
___

## How to install

#### Executable only

Go to the [releases](https://github.com/JessaTehCrow/VRC_control/releases) for this repository and download the latest release
![releases_img](images/releases.png)

Unpack the ZIP into a folder and run the .Exe

#### Repo clone

After you have cloned the repository, you can install the python dependecies using `pip -r requirements.txt` while in the directory of the repository.

After this is installed, you can go to the `src` folder, and run `main.py` with python >= 3.8

___

## How to use

***NOTE***
***Before you can use the program you will have to turn on OSC in vrchat***

![](images/osc.gif)

Upon starting the program, you will be prompted with which avatar you would like to choose within the terminal:
![](images/loaded.png)

You can select an avatar by typing the number infront of the name of the avatar you want to choose and pressing enter.

**Note:**
***If you have loaded this avatar before and have saved the settings, you will be prompted whether or not you want to load the save, or redo the setup.***

Open your web-browser and go to http://localhost (Only you can see this, no one else can).
Here, input which parameters / toggles you want to be able to change.

After you have selected all of your parameters, click on confirm and potentially `save options` to prevent the last step next time.
![select](images/param_select.png)

The page will refresh and load into the page where you can change the values.
![toggles](images/params.png)
___

## Sharing control with other people

You will have to either open a port on your router, or use a program to open your local network to others.

So you have two possibilities:

- Ngrok
- Portforwarding

### Port Forwarding

To open a port on your router, you will have to port-forward the tcp port 80 on your router.
Since it works differently for each router, i cannot make a standardized guide for this, you can find this on the internet. 

Search up `[router type] port-forwarding` (where `[router type]` is your router) on google or youtube.

### Ngrok Program

I personally like to use [ngrok](https://ngrok.com/download). 
Which allows me to open a specific port from my computer to the internet using a simple to use program.

**Note:**
***You will have to login to the ngrok services to use it. It is free and can have it running indefinitely. However, you can only run 1 instance of it per account: [ngrok setup](ngrok_setup.md)***

Once you have finished with the [ngrok setup](ngrok_setup.md), you can open the ngrok exe and type `ngrok http 80` to open port 80 to others (which is what we need now).

Once your session has started, you can share the url with other people.
![](images/ngrok.png)

Where in this case the url would be `https://aa9d-2001-1c00-513-5800-40a1-2d5c-d1c6-77f8.eu.ngrok.io` 
*(This will not be your url. Yours is different)*

And you can send this url to other people so they can access it too.
___

## Settings

The settings are located within the file `settings.json`
You can open this file and change the data within to update or change the settings for the program.

### Web Port

**note: you don't need to change this by default. This is only if you're already hosting a web-server on your device**

In the settings file, `"port": 80` indicates which port the program uses.
change `80` to whichever port you want to use for the program.


### OSC directory

The OSC directory is where all the data of the avatars is stored.
The default directory is in `"C:/Users/&USER&/AppData/LocalLow/VRChat/VRChat/OSC/"`.
This may change if you're running a different operating system, or have different drive prefixes.

In the settings file, `"directory": ". . ."` indicates which directory the program will look for the avatar files.

Change what comes after `"directory":` to what directory you want to use. Enclose the new directory in double quotes.

Example:
`"directory": "C:/new/directory/for/osc/"`

## Known problems

- Limited float slider (Max range 0-1, probably won't be fixed) 

## TODO
