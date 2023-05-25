char data = '3';
String results = "";
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
    // lcd.print(data);
    // Kiểm tra dữ liệu nhận được từ YOLO
    for (int i = 0; i < 4; i++) {
      if ((data & (1 << i)) != 0) {
        if (i == 0) {
          results += "Apple ";
        }
        if (i == 1) {
          results += "Banana ";
        }
        if (i == 2) {
          results += "Grapes ";
        }
        if (i == 3) {
          results += "Lemon ";
        }
      }
    }
    int str_len = results.length();
    if (results.length() <= 16) {
      lcd.print(results);
    } else {
      int last_space_pos = -1;
      int last_line_pos = 0;
      for (int i = 0; i < str_len; i++) {
        if (results.charAt(i) == ' ') {
          last_space_pos = i;
        }
        if ((i - last_line_pos) >= 16) {
          if (last_space_pos == -1 || (i - last_space_pos) >= 16) {
            last_space_pos = i;
          }
          lcd.setCursor(last_line_pos, 0);
          lcd.print(results.substring(last_line_pos, last_space_pos));
          last_line_pos = last_space_pos + 1;
          last_space_pos = -1;
          if (last_line_pos < str_len && results.charAt(last_line_pos) != ' ') {
            lcd.setCursor(last_line_pos, 1);
          }
        }
      }
      if (last_line_pos < str_len) {
      lcd.setCursor(0, 1);
      lcd.print(results.substring(last_line_pos));
      }
    }
    results = "";
  }
}
