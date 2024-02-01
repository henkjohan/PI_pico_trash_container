# PI_pico_trash_container
Use a PI pico to indicate which trash container will be emptied today or tomorrow.

# About
5 LEDs are connected to the PI pico to indicate the different types of trash to be collected

## trash types and LED pins
- gray (generic trash) container on pin 20
- green (organic) container on pin 19
- blue (paper) container on pin 18
- orange (packages and plastic) container on pin 17
- christmas tree on pin 16

## modes
Blinking LED means that this trash type is for tomorrow.

Solid LED means that this trash type is for today.

# Documentation link
https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

# Micropython for the PI pico

https://micropython.org/download/RPI_PICO/

# IDE for the PI pico to upload files and to debug

https://github.com/thonny/thonny/releases
