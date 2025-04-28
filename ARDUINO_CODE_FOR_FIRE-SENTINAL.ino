#include <Servo.h>

Servo servo360;  // 360° servo for scanning
Servo servo180;  // 180° servo for pushing CO₂ nozzle

const int yellowLED = 2;
const int blueLED   = 3;
const int redLED    = 4;
const int buzzer    = 5;

bool sweeping = true;

void setup() {
  Serial.begin(115200);

  servo360.attach(6);  // 360° servo on D6
  servo180.attach(7);  // 180° servo on D7

  pinMode(yellowLED, OUTPUT);
  pinMode(blueLED, OUTPUT);
  pinMode(redLED, OUTPUT);
  pinMode(buzzer, OUTPUT);

  digitalWrite(yellowLED, HIGH);
  delay(2000);
  digitalWrite(yellowLED, LOW);
  digitalWrite(blueLED, HIGH);  // Scanning mode
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');

    if (command == "FIRE") {
      digitalWrite(blueLED, LOW);
      digitalWrite(redLED, HIGH);
      digitalWrite(buzzer, HIGH);

      servo180.write(0);
      delay(1000);
      servo180.write(90);
      delay(1000);

      digitalWrite(buzzer, LOW);
    }

    else if (command == "STOP") {
      sweeping = false;
      servo360.write(90);  // Stop rotation
    }

    else if (command == "RESUME") {
      digitalWrite(redLED, LOW);
      digitalWrite(blueLED, HIGH);
      sweeping = true;
    }
  }

  if (sweeping) {
    servo360.write(100);  // Slow rotation
    delay(200);
  }
}
