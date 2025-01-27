# **RAH iRacing Overlay**

**iRacing Input Telemetry Overlay** is an open-source Python-based project that provides real-time telemetry from iRacing, displaying input data both through a web interface so you can put it on programs like OBS or screen overlay for using it on your game.

I just didn't wanted to pay for some overlays subcriptions to have the overlay that I actually wanted, so why not trying? I hope you feel the same, this is free of course ;)

<p align="center">
  <img src=https://github.com/RaulArcos/iracing-input-telemetry-overlay/blob/main/images/input-telemetry-gif.gif>
</p>

## **Table of Contents**

- [Compilation](#compilation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## **Compilation**

You can compile your own modified version, or make use of the precompiled one you can find on releases of this repo.

### **Prerequisites**

Before compiling, make sure you have the following installed:

- **Python 3.10+**: Ensure you have Python installed. You can download it from [here](https://www.python.org/downloads/).
- **iRacing SDK**: Install iRacing for telemetry data [here](https://github.com/kutu/pyirsdk.git).
  
### **1. Clone the Repository**

```bash
git clone https://github.com/RaulArcos/rah-iracing-overlay.git
cd iracing-input-telemetry-overlay
```

### **2. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **3. Compile into an EXE file**

```bash
pyinstaller RAH_Telemetry_Overlay.spec
```

## **Usage**

Just open the .exe file like a normal windows program, you will be welcomed by an easy interace to change the port (just in case you are using other overlay applications on the same port) and the framerate it should update.

<p align="center">
  <img src=https://github.com/user-attachments/assets/77a22083-824e-4408-a64e-4774321cbfa0>
</p>

Click start, on OBS, for example, add a web source and introduce the following URL: http://127.0.0.1:{your-selected-port}/input-telemetry

You should now see the telemetry, enter iRacing and enjoy!

## **Next Steps**

For now, my next focus will be on making it posible to show up as a overlay on screen, so monitor iRacing users can make use of it on their own games.

## **Contributing**

I hope you want to take part on this journey! Everyone is welcome to add diferent overlays to show interesting data like stadings positions, predicted points... you name it! These are the steps you should do to make this posible:

1. Fork the project.
2. Clone your forked repository to your local machine.
3. Create a new branch for your feature or fix:
 ```bash
git checkout -b feature-name
```
4. Commit your changes
```bash
git commit -m "Add some feature"
```
5. Pust your changes!
```bash
git push origin feature-name
```

## **License**
This project is licensed under the MIT License.
