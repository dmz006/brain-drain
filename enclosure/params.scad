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
below_board = 6.0;    // standoff height: THT leads, the CR2032 holder and buzzer on the bottom side
board_t     = 1.6;
above_board = 50.0;   // bay cards (C24): socket ~8 + card body 37.6 = ~46 above the board; their receptacles pass through the lid
lid_lip     = 3.0;    // skirt on the front and side edges only (the rear edge is the hinge)

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
oled_pos    = [50, 108];      // window centre in board coordinates: over the M.2 module (6 mm tall) at the
                              // front, on a 4-wire lead to J41; [] = above J41
fan_grille_d = 40;
vent_w      = 2.0;
vent_pitch  = 5.0;

// hinged lid (C22): knuckles along the rear top edge, snap latch at the front
hinge_pin_d = 2.0;    // filament pin
hinge_knuckle_d = 6.0;
hinge_knuckle_l = 12.0;
latch_bump_d = 1.6;

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

// (the v0 drive rack is gone: drives lie loose on the bench and connect with 22-pin cables, C21)
