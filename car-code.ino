#include <Bluepad32.h>
#include <uni.h>

// 允許連接的遊戲手把地址。
// 最多可以添加四個條目。
static const char * controller_addr_string = "A0:5A:5E:39:7C:3D";

ControllerPtr myControllers[BP32_MAX_GAMEPADS];

int m1_Lfin1 = 32; // 馬達1 前進
int m1_Lfin2 = 33; // 馬達1 後退
int m2_Rfin1 = 26; // 馬達2 前進
int m2_Rfin2 = 27; // 馬達2 後退
int m3_Lbin1 = 4;  // 馬達3 前進
int m3_Lbin2 = 16;  // 馬達3 後退
int m4_Rbin1 = 12;  // 馬達4 前進
int m4_Rbin2 = 13;  // 馬達4 後退
int value;

// 當新的遊戲手把連接時會調用此回調函數。
// 最多可以同時連接 4 個遊戲手把。
void onConnectedController(ControllerPtr ctl) {
    bool foundEmptySlot = false;
    for (int i = 0; i < BP32_MAX_GAMEPADS; i++) {
        if (myControllers[i] == nullptr) {
            Serial.printf("回調: 控制器已連接, 索引=%d\n", i);
            // 此外，還可以獲取某些遊戲手把屬性，例如：
            // 型號、廠商ID、產品ID、藍牙地址、標誌等。
            ControllerProperties properties = ctl->getProperties();
            Serial.printf("控制器型號: %s, VID=0x%04x, PID=0x%04x\n", ctl->getModelName().c_str(), properties.vendor_id,
                           properties.product_id);
            myControllers[i] = ctl;
            foundEmptySlot = true;
            break;
        }
    }
    if (!foundEmptySlot) {
        Serial.println("回調: 控制器已連接，但找不到空槽");
    }
}

void onDisconnectedController(ControllerPtr ctl) {
    bool foundController = false;

    for (int i = 0; i < BP32_MAX_GAMEPADS; i++) {
        if (myControllers[i] == ctl) {
            Serial.printf("回調: 控制器從索引=%d 斷開連接\n", i);
            myControllers[i] = nullptr;
            foundController = true;
            break;
        }
    }

    if (!foundController) {
        Serial.println("回調: 控制器斷開連接，但在 myControllers 中未找到");
    }
}

void dumpGamepad(ControllerPtr ctl) {
    Serial.printf(
        "idx=%d, 十字鍵: 0x%02x, 按鈕: 0x%04x, 左軸: %4d, %4d, 右軸: %4d, %4d, 煞車: %4d, 油門: %4d, "
        "其他: 0x%02x, 陀螺儀 x:%6d y:%6d z:%6d, 加速度計 x:%6d y:%6d z:%6d\n",
        ctl->index(),        // 控制器索引
        ctl->dpad(),         // 十字鍵
        ctl->buttons(),      // 按下按鈕的位掩碼
        ctl->axisX(),        // (-511 - 512) 左 X 軸
        ctl->axisY(),        // (-511 - 512) 左 Y 軸
        ctl->axisRX(),       // (-511 - 512) 右 X 軸
        ctl->axisRY(),       // (-511 - 512) 右 Y 軸
        ctl->brake(),        // (0 - 1023): 煞車按鈕
        ctl->throttle(),     // (0 - 1023): 油門（又稱為加速）按鈕
        ctl->miscButtons(),  // 按下的“其他”按鈕的位掩碼
        ctl->gyroX(),        // 陀螺儀 X
        ctl->gyroY(),        // 陀螺儀 Y
        ctl->gyroZ(),        // 陀螺儀 Z
        ctl->accelX(),       // 加速度計 X
        ctl->accelY(),       // 加速度計 Y
        ctl->accelZ()        // 加速度計 Z
    );
}

void dumpMouse(ControllerPtr ctl) {
    Serial.printf("idx=%d, 按鈕: 0x%04x, 滾輪=0x%04x, 增量 X: %4d, 增量 Y: %4d\n",
                   ctl->index(),        // 控制器索引
                   ctl->buttons(),      // 按下按鈕的位掩碼
                   ctl->scrollWheel(),  // 滾輪
                   ctl->deltaX(),       // (-511 - 512) 左 X 軸
                   ctl->deltaY()        // (-511 - 512) 左 Y 軸
    );
}

void dumpKeyboard(ControllerPtr ctl) {
    static const char* key_names[] = {
        // clang-format off
        // 為了避免此文件中噪聲過多，僅將少數按鍵映射到字符串。
        // 從 "A" 開始，偏移量為 4。
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
        "W", "X", "Y", "Z", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
        // 特殊按鍵
        "Enter", "Escape", "Backspace", "Tab", "Spacebar", "Underscore", "Equal", "OpenBracket", "CloseBracket",
        "Backslash", "Tilde", "SemiColon", "Quote", "GraveAccent", "Comma", "Dot", "Slash", "CapsLock",
        // 功能鍵
        "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
        // 光標和其他
        "PrintScreen", "ScrollLock", "Pause", "Insert", "Home", "PageUp", "Delete", "End", "PageDown",
        "RightArrow", "LeftArrow", "DownArrow", "UpArrow",
        // clang-format on
    };
    static const char* modifier_names[] = {
        // clang-format off
        // 從 0xe0 到 0xe7
        "左控制", "左移", "左選擇", "左元",
        "右控制", "右移", "右選擇", "右元",
        // clang-format on
    };
    Serial.printf("idx=%d, 按下的鍵: ", ctl->index());
    for (int key = Keyboard_A; key <= Keyboard_UpArrow; key++) {
        if (ctl->isKeyPressed(static_cast<KeyboardKey>(key))) {
            const char* keyName = key_names[key-4];
            Serial.printf("%s,", keyName);
       }
    }
    for (int key = Keyboard_LeftControl; key <= Keyboard_RightMeta; key++) {
        if (ctl->isKeyPressed(static_cast<KeyboardKey>(key))) {
            const char* keyName = modifier_names[key-0xe0];
            Serial.printf("%s,", keyName);
        }
    }
    Console.printf("\n");
}

void dumpBalanceBoard(ControllerPtr ctl) {
    Serial.printf("idx=%d,  TL=%u, TR=%u, BL=%u, BR=%u, 溫度=%d\n",
                   ctl->index(),        // 控制器索引
                   ctl->topLeft(),      // 左上秤
                   ctl->topRight(),     // 右上秤
                   ctl->bottomLeft(),   // 左下秤
                   ctl->bottomRight(),  // 右下秤
                   ctl->temperature()   // 溫度：用於調整秤值的精確度
    );
}

void processGamepad(ControllerPtr ctl) {
  int xValue = ctl->axisX();
  int yValue = ctl->axisY();
    // Control the car based on gamepad buttons
    if (ctl->y()) {
        driveForward();
    } else if (ctl->a()) {
        driveBackward();
    } else if (ctl->b()) {
        turnRight();
    } else if (xValue <-100) {
        Rleft();
    } else if (xValue >100) {
        Rright();
    }else if (ctl->x()) {
        turnLeft();
    } else {
        stopMotors(); // Stop if no button is pressed
    }
    dumpGamepad(ctl);
}

void processControllers() {
    for (auto myController : myControllers) {
        if (myController && myController->isConnected() && myController->hasData()) {
            if (myController->isGamepad()) {
                processGamepad(myController);
            } else {
                Serial.println("不支持的控制器");
            }
        }
    }
}

// Arduino 設置函數。運行在 CPU 1。
void setup() {
    pinMode(m1_Lfin1, OUTPUT);
    pinMode(m1_Lfin2, OUTPUT);
    pinMode(m2_Rfin1, OUTPUT);
    pinMode(m2_Rfin2, OUTPUT);
    pinMode(m3_Lbin1, OUTPUT);
    pinMode(m3_Lbin2, OUTPUT);
    pinMode(m4_Rbin1, OUTPUT);
    pinMode(m4_Rbin2, OUTPUT);
    Serial.begin(115200);
    Serial.printf("固件: %s\n", BP32.firmwareVersion());
    const uint8_t* addr = BP32.localBdAddress();
    Serial.printf("BD 地址: %2X:%2X:%2X:%2X:%2X:%2X\n", addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]);

    // 在你的 "setup" 中添加以下幾行：
    bd_addr_t controller_addr;

    // 解析人類可讀的藍牙地址。
    sscanf_bd_addr(controller_addr_string, controller_addr);

    // 注意，此地址將被添加到非易失性存儲（NVS）中。
    // 如果設備重新啟動，該地址仍將被存儲。
    // 添加重複值將不會有任何效果。
    // 最多可以在允許列表中添加四個條目。
    uni_bt_allowlist_add_addr(controller_addr);

    // 最後，啟用允許列表。
    // 與 "add_addr" 相似，其值將存儲在 NVS 中。
    uni_bt_allowlist_set_enabled(true);

    // 設置 Bluepad32 回調
    BP32.setup(&onConnectedController, &onDisconnectedController);

    // 當用戶執行“設備出廠重置”或類似操作時，應調用 "forgetBluetoothKeys()"。
    // 在 setup() 中調用 "forgetBluetoothKeys" 僅作為示例。
    // 忘記藍牙密鑰會防止“配對”的遊戲手把重新連接。
    // 但它也可能解決一些連接/重新連接問題。
    //BP32.forgetBluetoothKeys();

    // 為支持的遊戲手把啟用鼠標/觸控板支持。
    // 當啟用時，像 DualSense 和 DualShock4 這樣的控制器會生成兩個連接的設備：
    // - 第一個：遊戲手把
    // - 第二個，這是一個“虛擬設備”，是一個鼠標。
    // 默認情況下，它是禁用的。
    BP32.enableVirtualDevice(false);
}

void driveForward() {
    digitalWrite(m1_Lfin1, HIGH);
    digitalWrite(m1_Lfin2, LOW);
    digitalWrite(m2_Rfin1, HIGH);
    digitalWrite(m2_Rfin2, LOW);
    digitalWrite(m3_Lbin1, HIGH);
    digitalWrite(m3_Lbin2, LOW);
    digitalWrite(m4_Rbin1, HIGH);
    digitalWrite(m4_Rbin2, LOW);
}

void driveBackward() {
    digitalWrite(m1_Lfin1, LOW);
    digitalWrite(m1_Lfin2, HIGH);
    digitalWrite(m2_Rfin1, LOW);
    digitalWrite(m2_Rfin2, HIGH);
    digitalWrite(m3_Lbin1, LOW);
    digitalWrite(m3_Lbin2, HIGH);
    digitalWrite(m4_Rbin1, LOW);
    digitalWrite(m4_Rbin2, HIGH);
}

void turnRight() {
    digitalWrite(m1_Lfin1, HIGH);
    digitalWrite(m1_Lfin2, LOW);
    digitalWrite(m2_Rfin1, LOW);
    digitalWrite(m2_Rfin2, HIGH);
    digitalWrite(m3_Lbin1, LOW);
    digitalWrite(m3_Lbin2, HIGH);
    digitalWrite(m4_Rbin1, HIGH);
    digitalWrite(m4_Rbin2, LOW);
}

void turnLeft() {
    digitalWrite(m1_Lfin1, LOW);
    digitalWrite(m1_Lfin2, HIGH);
    digitalWrite(m2_Rfin1, HIGH);
    digitalWrite(m2_Rfin2, LOW);
    digitalWrite(m3_Lbin1, HIGH);
    digitalWrite(m3_Lbin2, LOW);
    digitalWrite(m4_Rbin1, LOW);
    digitalWrite(m4_Rbin2, HIGH);
}

void Rleft() {
    digitalWrite(m1_Lfin1, LOW);
    digitalWrite(m1_Lfin2, HIGH);
    digitalWrite(m2_Rfin1, HIGH);
    digitalWrite(m2_Rfin2, LOW);
    digitalWrite(m3_Lbin1, LOW);
    digitalWrite(m3_Lbin2, HIGH);
    digitalWrite(m4_Rbin1, HIGH);
    digitalWrite(m4_Rbin2, LOW);
}

void Rright() {
    digitalWrite(m1_Lfin1, HIGH);
    digitalWrite(m1_Lfin2, LOW);
    digitalWrite(m2_Rfin1, LOW);
    digitalWrite(m2_Rfin2, HIGH);
    digitalWrite(m3_Lbin1, HIGH);
    digitalWrite(m3_Lbin2, LOW);
    digitalWrite(m4_Rbin1, LOW);
    digitalWrite(m4_Rbin2, HIGH);
}

void stopMotors() {
    digitalWrite(m1_Lfin1, LOW);
    digitalWrite(m1_Lfin2, LOW);
    digitalWrite(m2_Rfin1, LOW);
    digitalWrite(m2_Rfin2, LOW);
    digitalWrite(m3_Lbin1, LOW);
    digitalWrite(m3_Lbin2, LOW);
    digitalWrite(m4_Rbin1, LOW);
    digitalWrite(m4_Rbin2, LOW);
}

// Arduino 循環函數。運行在 CPU 1。
void loop() {
    // 此調用獲取所有控制器的數據。
    // 在主循環中調用此函數。
    bool dataUpdated = BP32.update();
    if (dataUpdated)
        processControllers();

    // 主循環必須有某種“讓低優先級任務空間”的事件。
    // 否則，監視器將被觸發。
    // 如果你的主循環沒有一個，則只需添加一個簡單的 `vTaskDelay(1)`。
    // 詳細信息請參見：
    // https://stackoverflow.com/questions/66278271/task-watchdog-got-triggered-the-tasks-did-not-reset-the-watchdog-in-time

    //     vTaskDelay(1);
    delay(150);
}