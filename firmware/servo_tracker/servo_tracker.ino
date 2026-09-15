/*
 * servo_tracker.ino
 *
 * ESP32 pan-servo controller for face tracking.
 * Wiring: servo GND -> GND, servo signal -> D18, servo power -> Vin.
 *
 * Joins your WiFi network, then exposes a tiny HTTP server:
 *   GET /servo?angle=<0-180>   move to an absolute angle
 *   GET /center                move to 90 degrees
 *   GET /status                current angle as plain text
 *
 * Reachable at http://servotracker.local/ once on the network (mDNS),
 * so the PC side does not need to know its DHCP-assigned IP address.
 *
 * Requires the "ESP32Servo" library (Library Manager -> search ESP32Servo).
 */

#include <WiFi.h>
#include <ESPmDNS.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// ---- fill these in before flashing ----
const char *WIFI_SSID = "Y3A";
const char *WIFI_PASSWORD = "RCA@2024";
// ----------------------------------------

const char *MDNS_HOSTNAME = "servotracker"; // reachable at servotracker.local
const int SERVO_PIN = 18;                   // D18
const int SERVO_MIN_ANGLE = 0;
const int SERVO_MAX_ANGLE = 180;
const int SERVO_CENTER_ANGLE = 90;

// limits how fast the horn is allowed to move per update, so a big
// jump in the tracked face position doesn't jerk the mechanism.
// ~15 deg/sec: kept slow because a heavy camera platform overshoots and
// vibrates if the servo slews too fast.
const int MAX_STEP_DEGREES = 1;
const int STEP_INTERVAL_MS = 66;

Servo panServo;
WebServer server(80);

int currentAngle = SERVO_CENTER_ANGLE;
int targetAngle = SERVO_CENTER_ANGLE;
unsigned long lastStepMs = 0;

void handleServo() {
  if (!server.hasArg("angle")) {
    server.send(400, "text/plain", "missing angle param");
    return;
  }
  int angle = server.arg("angle").toInt();
  angle = constrain(angle, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE);
  targetAngle = angle;
  server.send(200, "text/plain", "OK angle=" + String(angle));
}

void handleCenter() {
  targetAngle = SERVO_CENTER_ANGLE;
  server.send(200, "text/plain", "OK centered");
}

void handleStatus() {
  server.send(200, "text/plain", String(currentAngle));
}

void setup() {
  Serial.begin(115200);

  ESP32PWM::allocateTimer(0);
  panServo.setPeriodHertz(50);
  panServo.attach(SERVO_PIN, 500, 2400);
  panServo.write(currentAngle);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected. IP: ");
  Serial.println(WiFi.localIP());

  if (MDNS.begin(MDNS_HOSTNAME)) {
    Serial.print("mDNS ready at http://");
    Serial.print(MDNS_HOSTNAME);
    Serial.println(".local/");
  } else {
    Serial.println("mDNS setup failed (use the IP above instead)");
  }

  server.on("/servo", handleServo);
  server.on("/center", handleCenter);
  server.on("/status", handleStatus);
  server.begin();
}

void loop() {
  server.handleClient();

  unsigned long now = millis();
  if (now - lastStepMs >= STEP_INTERVAL_MS && currentAngle != targetAngle) {
    lastStepMs = now;
    int diff = targetAngle - currentAngle;
    int step = constrain(diff, -MAX_STEP_DEGREES, MAX_STEP_DEGREES);
    currentAngle += step;
    panServo.write(currentAngle);
  }
}
