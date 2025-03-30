# PI_pico_trash_container
Use a PI pico to indicate which trash container will be emptied today or tomorrow.
5 LEDs are connected to the PI pico to indicate the different types of trash to be collected

## trash types and LED pins
- WHITE : (generic trash) gray container on GP20 - pin 26
- GREEN : (GFT : organic) container on GP19 - pin 25
- BLUE : (paper) container on GP18 - pin 24
- ORANGE : (PMD : packages and plastic) container on GP17 - pin 22
- RED : christmas tree and best_bag on GP16 - pin 21

## modes
- Blinking LED means that this trash type is for tomorrow.
- Solid LED means that this trash type is for today.

# Documentation link on micro python
https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

# Micropython download location for the PI pico
https://micropython.org/download/RPI_PICO/

# IDE for the PI pico to upload files and to debug
https://github.com/thonny/thonny/releases

# Build information
In the final build a signal tower was used. This signal tower operates on a common 12V, where every LED color needs to be pulled to ground.

## Power supply
As the signal tower needs to operate at 12V, a car to USB converter was used to generate the 5V for the PI pico. The 5V was connected to pin 40 of the board, and the ground to pin 38 of the board.

## Signal tower interface
5x BC547 transistors were used as emittor followers with 4k7 in line with the base to the pins of the PI pico to bridge the singal from the PI pico to the signal tower. 
