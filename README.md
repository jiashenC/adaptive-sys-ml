# Adaptive Machine Learning on IoT Devices
This repos serves as a demo for running deep learning neural network models on IoT devices. The goal 
of this demo is to show that with adaptive strategy implemented on IoT devices, the framework is able 
to provide better data integrity with the similar performance.

## Code Structure
```text
.
├── README.md
└── src
    ├── baseline
    │   ├── client.py
    │   ├── end.py
    │   ├── fast.py
    │   ├── resource
    │   │   └── message
    │   │       ├── avro-tools-1.8.2.jar
    │   │       ├── message.avdl
    │   │       └── message.avpr
    │   └── slow.py
    ├── s1
    │   ├── client.py
    │   ├── end.py
    │   ├── fast.py
    │   ├── resource
    │   │   └── message
    │   │       ├── avro-tools-1.8.2.jar
    │   │       ├── message.avdl
    │   │       └── message.avpr
    │   └── slow.py
    ├── s2
    │   ├── client.py
    │   ├── end.py
    │   ├── fast.py
    │   ├── resource
    │   │   └── message
    │   │       ├── avro-tools-1.8.2.jar
    │   │       ├── message.avdl
    │   │       └── message.avpr
    │   └── slow.py
    └── s3
        ├── client.py
        ├── end.py
        ├── resource
        │   └── message
        │       ├── avro-tools-1.8.2.jar
        │       ├── message.avdl
        │       └── message.avpr
        └── slow.py
```

* The `src` directory contains 4 directories, `baseline`, `s1`, `s2` and `s3`. Those 4 directories serve as 
purpose of different strategy baseline, strategy 1, strategy 2 and strategy 3. 
* In each sub directory, for example `baseline`, it contains an `end`, which collects data and calculate the 
stats for the whole pipeline system. `slow` simulates the heavier task referred as **Device B** and `fast`
simulates the lighter task referred as **Device A** in the report. Under `resource` directory, it contains 
the RPC message protocol header for nodes communication. `client` simulates the data from real world. It constantly
sends data to the next node in the pipeline system.
* For strategy 3, there is no `fast` node implemented, because the strategy simply copies all layers from one
device to another device.

## Environment Setup
### Dependencies
* TensorFlow == 1.5.0
* Python == 2.7.10
### Install Other Packages
I provide a requirements file for installing all packages by using below command.
```bash
pip install -r requirements.txt
```

## How To Run
### Understand how the system works
I run all experiments on Raspberry Pi environment, but the system should also work on any devices located 
in local area network. However, if the system is not based on Raspberry Pi, it will not output the same 
performance as I discuss in the report.

The IP addresses for devices to communicate with each other are hard coded for now. Please make sure you
change to according IP addresses assigned to your device before running the experiments. The port for serving
the traffic is also hardcoded for now, which is **12345**. Make sure to open this port for access before
running the system.

Each file `client`, `fast`, `slow` and `end` should be ran on different devices. For `baseline`, `s1` and `s2`,
`client` should send data to `fast`, `fast` should send data to `slow` and `slow` should send data to `end`.
For `s3`, the `client` should send data to 2 `slow` and `slow` should send data to `end`.

### Steps for running the experiments
Start servers first because model initialization takes time.
```bash
python end.py
python slow.py
python fast.py
```
Then start the client.
```bash
python client.py
```
Then you will see the stats output on the device which you run `end`

