#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <math.h>

// ───────── WIFI ─────────
const char* ssid = "EEE305C";
const char* password = "305@EEECL";

// ───────── MQTT ─────────
const char* mqtt_server = "broker.hivemq.com";
const char* topic = "arun/esp32/sensors";

// ───────── DHT ─────────
#define DHTPIN 23
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ───────── MQ-8 ─────────
#define MQ8_PIN 34
#define RL 10.0
#define RO 10.0

// ───────── OBJECTS ─────────
WiFiClient espClient;
PubSubClient client(espClient);

// ───────── LAST SENT VALUES ─────────
float last_temp = -1000;
float last_hum  = -1000;
float last_ppm  = -1000;

// ───────── THRESHOLDS ─────────
#define TEMP_DELTA 0.5
#define HUM_DELTA  2.0
#define PPM_DELTA  5.0

// ───────── WIFI CONNECT ─────────
void setup_wifi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

// ───────── MQTT RECONNECT ─────────
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting MQTT...");

    if (client.connect("ESP32_Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(2000);
    }
  }
}

// ───────── MQ-8 PPM CALCULATION ─────────
float getMQ8PPM() {
  int adc = analogRead(MQ8_PIN);

  float voltage = adc * (3.3 / 4095.0);
  float Rs = ((3.3 - voltage) / voltage) * RL;
  float ratio = Rs / RO;

  float ppm = pow(10, ((log10(ratio) - 0.42) / -0.48));

  return ppm;
}

// ───────── SETUP ─────────
void setup() {
  Serial.begin(115200);
  dht.begin();

  setup_wifi();

  client.setServer(mqtt_server, 1883);
}

// ───────── LOOP ─────────
void loop() {

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();
  float mq8_ppm = getMQ8PPM();

  if (isnan(temp) || isnan(hum)) {
    Serial.println("DHT sensor failed!");
    return;
  }

  static unsigned long last_publish_time = 0;
  unsigned long now = millis();

  // ───── CHECK CHANGE ─────
  bool changed = false;

  if (abs(temp - last_temp) > TEMP_DELTA) changed = true;
  if (abs(hum  - last_hum)  > HUM_DELTA)  changed = true;
  if (abs(mq8_ppm - last_ppm) > PPM_DELTA) changed = true;

  // ───── FORCE PUBLISH EVERY 10 SEC ─────
  bool forcePublish = (now - last_publish_time >= 10000);

  if (changed || forcePublish) {

    char payload[150];

    snprintf(payload, sizeof(payload),
             "{\"temp\":%.2f,\"hum\":%.2f,\"h2_ppm\":%.2f}",
             temp, hum, mq8_ppm);

    client.publish(topic, payload);

    Serial.println("Published:");
    Serial.println(payload);

    // update last values
    last_temp = temp;
    last_hum  = hum;
    last_ppm  = mq8_ppm;

    last_publish_time = now;
  }

  delay(2000);
}