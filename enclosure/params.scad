// brain-drain enclosure parameters. All mm. Board geometry comes from board.scad
// (generated from the KiCad file); everything here is the printed part.
include <board.scad>

// walls and clearances
wall       = 2.4;     // outer wall thickness
floor_t    = 2.4;     // tray floor
lid_t      = 2.4;     // lid plate
clear      = 1.0;     // board edge to inner wall
cut_clear  = 0.6;     // added around each connector cutout
fit        = 0.25;    // lid-to-tray sliding fit per side

// heights (z = 0 at the board top surface)
below_board = 6.0;    // standoff height: THT leads and the DIN jack legs
board_t     = 1.6;
above_board = 30.0;   // CM5 + cooler (~22), electrolytics (10.5), DIN body (12.9)
lid_lip     = 4.0;    // how far the lid skirt drops over the tray

// mounting
insert_d    = 3.5;    // M2.5 heat-set insert hole in the standoffs
insert_h    = 5.0;
standoff_d  = 7.0;
screw_d     = 2.8;    // clearance in the lid corners
corner_r    = 3.0;

// features on the lid
oled_win    = [24.0, 13.0];   // visible area of a 0.96" 128x64 module
oled_pcb    = [27.5, 27.5];   // module PCB, sits in a recess under the window
oled_hole_pitch = [23.0, 23.5];
oled_offset = [0, 0];         // move the window relative to J41 if wanted
fan_grille_d = 40;
vent_w      = 2.0;
vent_pitch  = 5.0;

// M.2 door on the RIGHT wall (x = board_w side)
door_w      = 26.0;   // opening width along y
door_h      = 8.0;    // opening height above board
door_z      = 0.5;
door_plug_t = 2.0;

// derived
inner_w = board_w + 2 * clear;
inner_h = board_h + 2 * clear;
outer_w = inner_w + 2 * wall;
outer_h = inner_h + 2 * wall;
tray_height = floor_t + below_board + board_t + above_board;   // to the top of the tray wall

// --- refinements (v0.2)
feet_d      = 8.5;    // rubber bumper pocket diameter (3M SJ5012 style, 8 mm)
feet_depth  = 1.0;
feet_inset  = 8.0;
bezel_t     = 1.6;    // OLED bezel plate thickness
bezel_post_d = 4.5;   // posts for the module's four M2 holes
bezel_post_h = 4.0;
hinge_pin_d = 2.0;    // filament pin
hinge_knuckle_d = 5.0;
door_lip    = 3.0;    // door overlaps the opening by this much all round

// drive rack: four vertical slots for 3.5" or 2.5" drives beside the unit
rack_slots  = 4;
rack_pitch  = 32.0;   // 26.1 mm 3.5" drive + air gap
rack_slot_w = 27.0;   // 3.5" drive thickness 26.1 + fit
rack_depth  = 60.0;   // how much of the 147 mm drive length is supported
rack_height = 40.0;
rack_wall   = 3.0;
rack_25_w   = 10.0;   // secondary groove for 2.5" drives (9.5 mm)
