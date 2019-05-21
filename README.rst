
Infopanel
=========

.. image:: https://travis-ci.org/partofthething/infopanel.svg?branch=master
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

It works with only one display so far, but more will be added if desired.


Installing it
-------------
To install, first install the dependencies:

* `RPI-RGB-LED-MATRIX  <https://github.com/hzeller/rpi-rgb-led-matrix>`_
* `RPI-RGB-LED-MATRIX python bindings  <https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python>`_

You may also need to run::

    sudo apt-get install libyaml-dev python-setuptools git python-matplotlib

We recommend running in a `virtual environment
<https://virtualenv.pypa.io/en/latest/>`_ just to keep the infopanel
environment from the rest of your system. If you want to do this optional step,
run something like this (with a path of your choosing)::

    python -m virtualenv /path/to/infopanel-venv
    source /path/to/infopanel-venv/bin/activate

The source code is `hosted on github
<https://github.com/partofthething/infopanel>`_. Grab it and install
*infopanel*::

    git clone https://github.com/partofthething/infopanel.git
    cd infopanel
    python setup.py install

	git clone git@github.com:partofthething/infopanel.git
	cd infopanel
	python setup.py install

.. note::

	If you don't have git, you can just download the source directly from
	`here <https://github.com/partofthething/infopanel/archive/master.zip>`_.


Using it
--------
To use it you need to set up a configuration file that describes the screen, data sources, 
and various sprites, scenes (collections of sprites), and modes (sets of scenes). If you
have a MQTT server for command and control you can point to it. Otherwise, skip that section.

.. code:: yaml

    mqtt:
      broker: yourserver.com
      port: 8883
      client_id: screen
      keepalive: 60
      username: user
      password: pass
      certificate: /etc/ssl/certs/DST_Root_CA_X3.pem
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
            brightness: 50
        - traffic:
            duration: 10 

    global:
        font_dir: $RPI_RGB_LED_MATRIX/fonts
        
        
and run (with sudo if using RGB matrix on a Raspberry Pi):

.. code:: bash

    sudo python -m infopanel --config ~/.infopanel/infopanel.yaml
    

There are a few animations built in (e.g. giraffes), but you will have lots of fun
building your own sprites and animations. See ``tests/test_config.yaml`` for full examples of this. 

.. note:: If you set ``brightness`` in the mode section, it will constantly override any
    adjustments you make via the MQTT controller. Leave it out for useful remote control.

