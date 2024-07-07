#include <Servo.h>

Servo myServo;
const int servoPin = 9; // servo motorun bağlı olduğu pin bu pine bağla veya senin pine göre değiş

void setup() {
  Serial.begin(9600);
  myServo.attach(servoPin);
  myServo.write(0); // servo motorumuzun başlangıç pozisyonu
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // komutun başındaki ve sonundaki boşlukları temizler

    if (command == "open") {
      myServo.write(90); // kapıyı açar (90 derece)
    } else if (command == "close") {
      myServo.write(0); // kapıyı kapatır (0 derece)
    }
  }