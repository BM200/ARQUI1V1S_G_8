/*
 * ARDUINO ESCLAVO
 */

const int PIN_MQ135   = A0;  // Sensor de gas
const int PIN_SUELO_1 = A1;  // Humedad suelo Área 1
const int PIN_SUELO_2 = A2;  // Humedad suelo Área 2
const int PIN_LDR     = A4;  // Sensor de luz

// Intervalo de envío. La Pi controla su propio ritmo de lectura,
// pero 2000 ms evita saturar el buffer serial innecesariamente.
const unsigned long INTERVALO_MS = 2000;

void setup() {
  Serial.begin(9600);
}

void loop() {
  // Lectura doble con pequeña pausa: la primera lectura tras
  // cambiar de canal del ADC puede venir contaminada por el
  // canal anterior (impedancia del multiplexor del ATmega).
  int mq135   = leerEstable(PIN_MQ135);
  int suelo1  = leerEstable(PIN_SUELO_1);
  int suelo2  = leerEstable(PIN_SUELO_2);
  int ldr     = leerEstable(PIN_LDR);

  // Línea CSV: gas,suelo1,suelo2,luz
  Serial.print(mq135);
  Serial.print(",");
  Serial.print(suelo1);
  Serial.print(",");
  Serial.print(suelo2);
  Serial.print(",");
  Serial.println(ldr);   // println agrega el \n que Python espera

  delay(INTERVALO_MS);
}

// Descarta la primera lectura y promedia 3 para reducir ruido
int leerEstable(int pin) {
  analogRead(pin);       // lectura de descarte
  delay(5);
  long suma = 0;
  for (int i = 0; i < 3; i++) {
    suma += analogRead(pin);
    delay(2);
  }
  return (int)(suma / 3);
}
