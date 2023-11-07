

// This example checks the state of the rotary encoder using interrupts and in the loop() function.
// The current position and direction is printed on output when changed.

// Hardware setup:
// Attach a rotary encoder with output pins to
// * 2 and 3 on Arduino UNO. (supported by attachInterrupt)
// * A2 and A3 can be used when directly using the ISR interrupts, see comments below.
// * D5 and D6 on ESP8266 board (e.g. NodeMCU).
// Swap the pins when direction is detected wrong.
// The common contact should be attached to ground.
//
// Hints for using attachinterrupt see https://www.arduino.cc/reference/en/language/functions/external-interrupts/attachinterrupt/

#include <Arduino.h>
#include <RotaryEncoder.h>
#include <util/atomic.h>

#if defined(ARDUINO_AVR_UNO) || defined(ARDUINO_AVR_NANO_EVERY)
// Example for Arduino UNO with input signals on pin 2 and 3
#define PIN_IN1 2
#define PIN_IN2 3

#elif defined(ESP8266)
// Example for ESP8266 NodeMCU with input signals on pin D5 and D6
#define PIN_IN1 D5
#define PIN_IN2 D6

#endif

// A pointer to the dynamic created rotary encoder instance.
// This will be done in setup()
RotaryEncoder *encoder = nullptr;

#if defined(ARDUINO_AVR_UNO) || defined(ARDUINO_AVR_NANO_EVERY)
// This interrupt routine will be called on any change of one of the input signals
void checkPosition()
{
  encoder->tick(); // just call tick() to check the state.
}

#elif defined(ESP8266)
/**
 * @brief The interrupt service routine will be called on any change of one of the input signals.
 */
IRAM_ATTR void checkPosition()
{
  encoder->tick(); // just call tick() to check the state.
}

#endif

const int Signal_PIN = 5;
const int Inc_Signal_PIN = 9;

long GlobalCounter=0;
int x;
char delim[] = " ";

struct Part{
  bool avail;
  int Class;
  long Length;
  long Inital_Pos;
};

bool State_sollLesen = LOW;
bool State_POST_sollLesen = LOW;

int List_Lenth=30;
struct Part List[30];
int State=0;

long getPosition(){
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE){
  long pos=(long)((float)(encoder->getPosition())/720*114);
  return pos;
  }
}

void ChangeSignalPIN(){
  if (State==0){
    SignalPin_HIGH();
    State=1;
  }
  else {
    SignalPin_LOW();
    State=0;
  }
}

void SignalPin_HIGH(){
    //analogWrite(Signal_PIN, 168);
    digitalWrite(Signal_PIN,HIGH);
}

void SignalPin_LOW(){
    //analogWrite(Signal_PIN, 0);
    digitalWrite(Signal_PIN,LOW);
}

int SaveInPartList(int cls,int len){
  for(int i=0; i<List_Lenth; i++){
      if(List[i].avail==true){
          List[i].Class=cls;
          List[i].Length=len;
          ATOMIC_BLOCK(ATOMIC_RESTORESTATE){
          List[i].Inital_Pos=getPosition();
          }
          List[i].avail=false;
          i=List_Lenth;
      }
  }
}

int initilizeParts(){
      String rxString = "";
      String strArr[2]; //Set the size of the array to equal the number of values you will be receiveing.
      //Keep looping until there is something in the buffer.
      while (Serial.available()) {
      //Delay to allow byte to arrive in input buffer.
      delay(2);
      //Read a single character from the buffer.
      char ch = Serial.read();
      //Append that single character to a string.
      rxString+= ch;
      }
      int stringStart = 0;
      int arrayIndex = 0;
      for (int i=0; i < rxString.length(); i++){
      //Get character and check if it's our "special" character.
      if(rxString.charAt(i) == ','){
      //Clear previous values from array.
      strArr[arrayIndex] = "";
      //Save substring into array.
      strArr[arrayIndex] = rxString.substring(stringStart, i);
      //Set new string starting point.
      stringStart = (i+1);
      arrayIndex++;
      }
      }
      //Put values from the array into the variables.
      String value1 = strArr[0];
      String value2 = strArr[1];
      //Convert string to int if you need it.
      int Value1 = value1.toInt();
      int Value2 = value2.toInt();
      SaveInPartList(Value1, Value2);
  }

void checkPartList(){
      for(int i=0; i<List_Lenth; i++){
          ATOMIC_BLOCK(ATOMIC_RESTORESTATE){
            if(getPosition()-List[i].Inital_Pos >= List[i].Length && List[i].avail==false){
                  ChangeSignalPIN();
                  
                  Serial.println(List[i].Class);
                  //Serial.println(List[i].Length);
                  //Serial.println(GlobalCounter-List[i].Inital_Pos);
                  //Serial.println("done--------------------------------------------------------------");
                  List[i].avail=true;
            }
          }
      } 
}
void READ_SERIAL(){
      if(Serial.available()){
        initilizeParts();
      }
      Serial.flush();
}

void setup()
{
  Serial.begin(115200);
  Serial.setTimeout(1);
  // setup the rotary encoder functionality
  pinMode(Signal_PIN, OUTPUT);
  pinMode(Inc_Signal_PIN, INPUT); 
  SignalPin_LOW();

  encoder = new RotaryEncoder(PIN_IN1, PIN_IN2, RotaryEncoder::LatchMode::TWO03);
  
  //attachInterrupt(digitalPinToInterrupt(9), READ_SERIAL, CHANGE);
  
  // register interrupt routine
  attachInterrupt(digitalPinToInterrupt(PIN_IN1), checkPosition, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_IN2), checkPosition, CHANGE);
  
  for(int i=0; i<List_Lenth; i++){
  List[i].avail=true;  
  }
  
} // setup()


// Read the current position of the encoder and print out when changed.
void loop()
{
      //GlobalCounter++;
      State_sollLesen = digitalRead(Inc_Signal_PIN);
      if (State_sollLesen != State_POST_sollLesen){
          READ_SERIAL();
          State_POST_sollLesen = State_sollLesen;
          
      }
      
      
      checkPartList();
      //Serial.println(getPosition());
      //Serial.println(GlobalCounter);
      //delay(10);
} // loop ()
