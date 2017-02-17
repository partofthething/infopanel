
Infopanel
=========

.. image:: https://travis-ci.org/partofthething/infopanel.svg?branch=develop
    :target: https://travis-ci.org/partofthething/infopanel
    
Infopanel is a tool to organize and display live information from many sources (various sensors, 
etc.), simple animations, images, animated gifs and anything else on various screens. In 
particular, it is suitable for displaying various scenes on a RGB LED Matrix. 

The code for this project, as well as the issue tracker, etc. is
`hosted on GitHub <https://github.com/partofthething/infopanel>`_.
The full documentation is hosted at https://partofthething.com/infopanel.

What is it?
-----------
Infopanel is useful as a component in a home automation system, as a fun decoration, 
or even as a system monitoring display. It can show you weather, traffic conditions, 
jokes, basically anything you can send to it. It gets data from MQTT, which 
can come from all sorts of sources. 

.. raw:: html

    <video autoplay loop> 
        <source src="https://partofthething.com/infopanel/_static/horses.webm" type="video/webm">
    Your browser does not support the video tag.
    </video> 

It works with only one display so far, but more will be added if desired:

* `RPI-RGB-led-matrix <https://github.com/hzeller/rpi-rgb-led-matrix>`_.


Installing it
-------------

Directly from source::

	git clone git@github.com:partofthething/infopanel.git
	cd infopanel
	python setup.py install

.. note::

	If you don't have git, you can just download the source directly from
	`here <https://github.com/partofthething/infopanel/archive/master.zip>`_.


Using it
--------
To use it you need to set up a configuration file that describes the screen, data sources, 
and various sprites, scenes (collections of sprites), and modes (sets of scenes).

.. code:: yaml

    mqtt:
      broker: test.com
      port: 8883
      client_id: screen
      keepalive: 60
      username: user
      password: pass
      certificate: /etc/ssl/certs/DST_Root_CA_X3.pem
      protocol: 3.1
      topic: house/screen/#
    
    RGBMatrix:
      led-rows: 32
      led-chain: 2
      led-parallel: 1
      led-pwm-bits: 11
      led-brightness: 100
      led-gpio-mapping: adafruit-hat-pwm
      led-scan-mode: 1
      led-pwm-lsb-nanoseconds: 130
      led-show-refresh: false
      led-slowdown-gpio: 0
      led-no-hardware-pulse: false
      
    sprites: 
      I90:
          type: Duration    
          label: I90
          low_val: 13.0
          high_val: 23.0
          data_label: travel_time_i90

    scenes:
      flag: 
          type: Image
          path: $HOME/.infopanel/flag.ppm
      cat: 
          type: AnimatedGif
          path: $HOME/.infopanel/rainbow_cat.gif
          
     modes: 
      morning: 
        - giraffes:
            duration: 15
        - traffic:
            duration: 10 

    global:
        font_dir: $RPI_RGB_LED_MATRIX/fonts
        
        
and run (with sudo if using RGB matrix on a Raspberry Pi):

.. code:: bash

    sudo python -m infopanel --config ~/.infopanel/infopanel.yaml
    

There are a few animations built in (e.g. giraffes), but you will have lots of fun
building your own sprites and animations. See ``tests/test_config.yaml`` for full examples of this. 
    
