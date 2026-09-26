// brain-drain enclosure parameters. All mm. Board geometry comes from board.scad
// (generated from the KiCad file); everything here is the printed part.
include <board.scad>

// walls and clearances
wall       = 2.4;     // outer wall thickness
floor_t    = 2.4;     // tray floor
lid_t      = 2.4;     // lid plate
clear      = 1.0;     // board edge to inner wall
rear_ext   = 16.0;    // extra depth behind the board: the 45 mm bay cards overhang its rear edge by 15.3 mm (option A, 2026-09-24)
cut_clear  = 0.6;     // added around each connector cutout
fit        = 0.25;    // lid-to-tray sliding fit per side

// heights (z = 0 at the board top surface)
below_board = 6.0;    // standoff height: THT leads, the CR2032 holder and buzzer on the bottom side
board_t     = 1.6;
above_board = 50.0;   // bay cards (C24): socket 11.25 + card body 37.6 = 48.9 above the board; the plugs pass through the lid windows
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
oled_pos    = [board_w - 50, 108];      // window centre in board coordinates: over the M.2 module (6 mm tall) at the
                              // front, on a 4-wire lead to J41; [] = above J41
fan_grille_d = 40;
vent_w      = 2.0;
vent_pitch  = 5.0;

// hinged lid (C22): knuckles along the rear top edge, snap latch at the front
hinge_pin_d = 2.0;    // filament pin
hinge_knuckle_d = 6.0;
hinge_knuckle_l = 12.0;
latch_bump_d = 1.6;

// bay-card retention (C30): a comb of ribs under the lid between the cards' receptacles, and blocks with a groove under each
// card's rear overhang in the tray. Card geometry from the placed 3D model: the card slab is centred 5.4 mm behind the window
// centre (window x from board.scad), the receptacle housing runs 9.5 mm from the slab toward the next slot.
card_off     = 5.4;    // window centre to card centre, along x (mirrored frame: toward +x)
card_t       = 1.6;
comb_depth   = 8.0;    // rib height below the lid plate (card top edge is 1.1 mm below the plate)
comb_gap     = 0.4;    // clearance to the card back face and to the next receptacle housing
comb_y       = [-14.0, 28.0];   // rib extent along the board y (window is -14.9 .. 29.3; LEDs start at y 29.1)
card_over    = 15.3;   // how far the 45 mm cards overhang the board's rear edge
card_shoulder_z = 11.25;   // card shoulder (bottom edge outside the 20.3 mm tab) above the board top surface
support_w    = 4.4;    // overhang support block width along x
support_groove = 2.0;  // groove for the card edge
support_groove_d = 3.0;
support_gap  = 0.5;    // card shoulder to groove floor

// lid artwork, engraved into the outer face (impression, prints on the bed face)
engrave_d    = 0.6;
logo_pos     = [100, 60];   // board x (mirrored frame) and y of the artwork centre
logo_mm      = 68;          // width of the octopus
name_text    = "BRAIN-DRAIN";
name_size    = 7;
name_dy      = 24;          // name centre below the logo centre
sub_text     = "NIST 800-88 DISK SANITIZER";
sub_size     = 3;
sub_dy       = 31;

// derived
inner_w = board_w + 2 * clear;
inner_h = board_h + 2 * clear + rear_ext;
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
