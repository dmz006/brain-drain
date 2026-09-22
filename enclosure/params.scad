// brain-drain enclosure parameters. All mm. Board values are placeholders
// until hardware/brain-drain.kicad_pcb exists; then board.scad is generated.

board_x = 160;      // PCB outline
board_y = 100;
board_t = 1.6;
wall    = 2.4;
clear   = 1.0;      // board-to-wall clearance
standoff_h = 6;     // board underside to floor
lid_h   = 28;       // inside height above board (CM4 + heatsink + OLED module)
insert_d = 3.5;     // M2.5 heat-set insert hole
corner_r = 3;

// UI (top face)
oled_w = 27; oled_h = 27;     // 0.96" module outline; window cut is smaller
oled_win_w = 24; oled_win_h = 13;
dip_w = 21; dip_h = 10;       // 8-way DIP slot
led_d = 3.2;

// Rear face
sata22_w = 26; sata22_h = 7;  // 22-pin receptacle window, 4 of them
sata22_pitch = 28;
