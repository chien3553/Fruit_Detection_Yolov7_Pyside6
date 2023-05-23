char data = '3';
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27,16,2);


byte degree[8] = {
  0B01110,
  0B01010,
  0B01110,
  0B00000,
  0B00000,
  0B00000,
  0B00000,
  0B00000
};

void setup() {
  Serial.begin(9600);
  lcd.init();  
  lcd.backlight();
  lcd.print("Project AI Robot");
  lcd.setCursor(0,1);
  lcd.print("Fruits Detection");
}

void loop() {
  
  // Đọc dữ liệu từ Serial communication
  if (Serial.available() > 0) {
    int data = Serial.read();
    lcd.clear();
    // Kiểm tra dữ liệu nhận được từ YOLO
    // Nếu là Táo, hiện thị Apple
    if (data == '0') {
      lcd.setCursor(0,0);
      lcd.print("Apple"); 
      
    }
    // Nếu là Chuối, hiện thị Banana
    else if (data == '1') {
      lcd.setCursor(0,0);
      lcd.print("Banana");
    
    }
    // Nếu là Nho, hiện thị Grapes
    else if (data == '2') {
      lcd.setCursor(0,0);
      lcd.print("Grapes");
    
    }

    // Nếu là Chanh, hiển thị Lemon
    else if (data == '3') {
      lcd.setCursor(0,0);
      lcd.print("Lemon");
    
    }
  }
}
