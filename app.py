#app2.py
#written to match Azure IOT Central device viewhumnfan v2
#

import asyncio
import os
import json
import datetime
import random
import bme280

from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import MethodResponse
from azure.iot.device import Message

from humi import Humi

from time import time, ctime
from os import system

h = Humi(45, 37)    # (humLimit, GPIO pin)
delay = 600
pin = 4
    
async def main():
    provisioning_host = os.getenv("AZUREv2_PROVISIONING_HOST")
    id_scope = os.getenv("AZUREv2_ID_SCOPE")
    registration_id = os.getenv("AZUREv2_REGISTRATION_ID")
    symmetric_key = os.getenv("AZUREv2_SYMMETRIC_KEY")

 


    # All the remaining code is nested within this main function

    async def register_device():
        provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
          provisioning_host=provisioning_host,
          registration_id=registration_id,
          id_scope=id_scope,
          symmetric_key=symmetric_key,
        )

        registration_result = await provisioning_device_client.register()

        print(f'Registration result: {registration_result.status}')

        return registration_result

    async def connect_device():
        device_client = None
        try:
          registration_result = await register_device()
          if registration_result.status == 'assigned':
            device_client = IoTHubDeviceClient.create_from_symmetric_key(
              symmetric_key=symmetric_key,
              hostname=registration_result.registration_state.assigned_hub,
              device_id=registration_result.registration_state.device_id,
            )
            # Connect the client.
            await device_client.connect()
            print('Device connected successfully')
        finally:
          return device_client

    
    async def send_telemetry():
        print(f'Sending telemetry from the provisioned device every {delay} seconds')
        while True:
            
            t,p,rH = bme280.readBME280All()
            h.FanControl(rH)
            print("Reading @ {3}: {0:3.2f}gC, {1:4.0f}hPa, {2:2.1f}rH   ".format(t, p, rH, ctime())) 
            payload = json.dumps({'TemperatureData': t, 'HumidityData': round(rH,2)})
            msg = Message(payload)
            await device_client.send_message(msg, )
            #print(f'Sent message: {msg}')

            await asyncio.sleep(delay) 


    # function to handle property updates sent from your IoT Central application
    async def humiditylimit_setting(value, version):
      await asyncio.sleep(1)
      print(f'Setting humidity limit value {value} - {version}')
      h.UpdateHumiLimit(value['value'])
      await device_client.patch_twin_reported_properties({'name' : {'value': value['value'], 'status': 'completed', 'desiredVersion': version}})
    
    async def logginginterval_setting(value, version):
      await asyncio.sleep(1)
      print(f'Setting Logging interval {value} - {version}')
      global delay
      delay = value['value']
      #print(f'Loggin inteval set to {delay} ')
      await device_client.patch_twin_reported_properties({'name' : {'value': value['value'], 'status': 'completed', 'desiredVersion': version}})

#    async def name_setting(value, version):
#      await asyncio.sleep(1)
#      print(f'Setting name value {value} - {version}')
#      await device_client.patch_twin_reported_properties({'name' : {'value': value['value'], 'status': 'completed', 'desiredVersion': version}})

#    async def brightness_setting(value, version):
#      await asyncio.sleep(5)
#      print(f'Setting brightness value {value} - {version}')
#      await device_client.patch_twin_reported_properties({'brightness' : {'value': value['value'], 'status': 'completed', 'desiredVersion': version}})

    settings = {
        'HumidityLimit' : humiditylimit_setting , 
        'LoggingInterval' : logginginterval_setting
#      'name': name_setting,
#      'brightness': brightness_setting
    }

    # define behavior for receiving a twin patch
    async def twin_patch_listener():
      while True:
        patch = await device_client.receive_twin_desired_properties_patch() # blocking
        to_update = patch.keys() & settings.keys()
        await asyncio.gather(
          *[settings[setting](patch[setting], patch['$version']) for setting in to_update]
        )


# Define behavior for halting the application
    def stdin_listener():
        while True:
            selection = input('Press Q to quit\n')
            if selection == 'Q' or selection == 'q':
                print('Quitting...')
                break

    device_client = await connect_device()

    if device_client is not None and device_client.connected:
        print('Send reported properties on startup')
        await device_client.patch_twin_reported_properties({'state': 'true'})
        tasks = asyncio.gather(
          send_telemetry(),
#          command_listener(),
          twin_patch_listener(),
        )
            

        # Run the stdin listener in the event loop
        loop = asyncio.get_running_loop()
        user_finished = loop.run_in_executor(None, stdin_listener)

        # Wait for user to indicate they are done listening for method calls
        await user_finished

        # Cancel tasks
        tasks.add_done_callback(lambda r: r.exception())
        tasks.cancel()
        await device_client.disconnect()
      
    else:
        print('Device could not connect')


if __name__ == '__main__':
    asyncio.run(main())

            



