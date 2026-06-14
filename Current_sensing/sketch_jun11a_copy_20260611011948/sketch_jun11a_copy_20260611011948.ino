#include <Wire.h>
#include <Adafruit_INA219.h>
 
Adafruit_INA219 ina219;
 
void setup(void)
{
  Serial.begin(115200);
  while (!Serial) 
  {
    delay(1);
  }
 
  // Initialize the INA219.
  if (! ina219.begin())
  {
    Serial.println("Failed to find INA219 chip");
    while (1) 
    {
      delay(10);
    }
  }
  // To use a slightly lower 32V, 1A range (higher precision on amps):
  //ina219.setCalibration_32V_1A();
  // Or to use a lower 16V, 400mA range, call:
  //ina219.setCalibration_16V_400mA();
 
  Serial.println("Measuring current with INA219 ...");
}
 
void loop(void)
{
  float current_mA = 0;
  // float shuntvoltage = 0;
  // float busvoltage = 0;
  // float loadvoltage = 0;
  // float power_mW = 0;
 
  current_mA = ina219.getCurrent_mA();
  // shuntvoltage = ina219.getShuntVoltage_mV();
  // busvoltage = ina219.getBusVoltage_V();
  // power_mW = ina219.getPower_mW();
  // loadvoltage = busvoltage + (shuntvoltage / 1000);
 
  Serial.print(current_mA); Serial.println(",");
 
  delay(10);
}
