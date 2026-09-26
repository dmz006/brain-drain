// brain-drain enclosure v2 ("brain box", C22): tray (bottom) and a hinged lid (top) that pops
// open for the M.2 SSD. Board origin: x from the left, y from the REAR edge (the four drive
// cables), z from the board top surface. Right wall: DIN power, USB-C, microSD. Left wall: the
// CM5 antenna edge, vents only. Lid: OLED window, DIP slot, LED holes, fan grille (passive cooler,
// grille for convection). Hinge along the rear top edge, snap latch at the front.
//   openscad -D part=\"tray\" -o stl/tray.stl shell.scad
//   openscad -D part=\"lid\"  -o stl/lid.stl  shell.scad
//   openscad -D part=\"door\" -o stl/door.stl shell.scad
include <params.scad>
include <logo.scad>
use <refinements.scad>

part = "all";   // all | tray | lid
$fn = 48;

// --------------------------------------------------------------- helpers
// board coordinates -> enclosure coordinates. The rear edge (board y = 0) is the
// enclosure's -y wall; z = 0 is the tray floor's underside.
z_board_top = floor_t + below_board + board_t;
function bx(x) = wall + clear + x;
function by(y) = wall + clear + rear_ext + y;
// the lid is modelled with local y = 0 at the tray FRONT (it is turned over about x onto the tray), so a board y maps to outer_h - by(y)
function lby(y) = outer_h - by(y);
slot_x_min = min([for (f = board_features) if (f[1] == "slot") f[2]]);

module rounded_box(w, h, z, r) {
    linear_extrude(z) offset(r) offset(-r) square([w, h]);
}

module feature(kind) {
    // binds the matching feature row to $f for the child module (children() takes no arguments)
    for (f = board_features) if (f[1] == kind) let ($f = f) children();
}

// --------------------------------------------------------------- cutouts
module rear_cutouts() {
    // connector faces poke through the -y wall; each is a box from the board top up
    feature("rear") let (x = bx($f[2]), w = $f[5] + 2 * cut_clear, h = $f[6] + 2 * cut_clear, z = $f[7])
        translate([x - w / 2, -1, z_board_top + z - cut_clear])
            cube([w, wall + 2, h]);
}

module left_cutouts() {
    feature("left") let (y = by($f[3]), w = $f[5] + 2 * cut_clear, h = $f[6] + 2 * cut_clear, z = $f[7])
        translate([-1, y - w / 2, z_board_top + z - cut_clear])
            cube([wall + 2, w, h]);
}

module right_cutouts() {
    feature("right") let (y = by($f[3]), w = $f[5] + 2 * cut_clear, h = $f[6] + 2 * cut_clear, z = $f[7])
        translate([outer_w - wall - 1, y - w / 2, z_board_top + z - cut_clear])
            cube([wall + 2, w, h]);
}

module standoffs() {
    for (h = board_holes)
        translate([bx(h[0]), by(h[1]), floor_t - 0.01])
            difference() {
                cylinder(d = standoff_d, h = below_board + 0.01);
                translate([0, 0, below_board - insert_h]) cylinder(d = insert_d, h = insert_h + 1);
            }
}

module side_vents() {
    // vent slots in the RIGHT wall (the CM5 antenna edge: plastic only, no metal) and the rear wall
    n = floor((inner_h - 30) / vent_pitch);
    for (i = [0 : n - 1])
        translate([outer_w - wall - 1, wall + 15 + i * vent_pitch, z_board_top + 6])
            cube([wall + 2, vent_w, 24]);
    m = floor((inner_w - 30) / vent_pitch);
    for (i = [0 : m - 1])
        translate([wall + 15 + i * vent_pitch, -1, z_board_top + 8])
            cube([vent_w, wall + 2, 24]);
}

// hinge along the rear top edge: tray knuckles at 1/4 and 3/4, lid knuckles between them
module knuckle(x0, len) {
    translate([x0, -hinge_knuckle_d / 2, tray_height]) rotate([0, 90, 0]) cylinder(d = hinge_knuckle_d, h = len);
    translate([x0, -hinge_knuckle_d / 2, tray_height - hinge_knuckle_d / 2]) cube([len, hinge_knuckle_d / 2 + wall, hinge_knuckle_d / 2]);
}
module hinge_bore() {
    translate([-1, -hinge_knuckle_d / 2, tray_height]) rotate([0, 90, 0]) cylinder(d = hinge_pin_d + 0.3, h = outer_w + 2);
}
function tray_knuckles() = [[outer_w * 0.25 - hinge_knuckle_l - 0.3, hinge_knuckle_l], [outer_w * 0.25 + 0.3, hinge_knuckle_l],
                            [outer_w * 0.75 - hinge_knuckle_l - 0.3, hinge_knuckle_l], [outer_w * 0.75 + 0.3, hinge_knuckle_l]];


// blocks under each card's rear overhang (C30): the card's shoulder sits 0.5 mm above a groove, so a knock or a pulled cable
// cannot rock the card down. They stand on the tray floor, clear of the rear wall (vents) and of the board edge.
module card_supports() {
    z_top = z_board_top + card_shoulder_z - support_gap + support_groove_d;
    y_lo = by(-card_over) + 0.9; y_hi = by(0) - 0.8;
    feature("slot") let (c = $f[2] + card_off)
        difference() {
            translate([bx(c) - support_w / 2, y_lo, floor_t - 0.01]) cube([support_w, y_hi - y_lo, z_top - floor_t + 0.01]);
            translate([bx(c) - support_groove / 2, y_lo - 1, z_top - support_groove_d]) cube([support_groove, y_hi - y_lo + 2, support_groove_d + 1]);
        }
}

// --------------------------------------------------------------- tray
module tray() {
    difference() {
        rounded_box(outer_w, outer_h, tray_height, corner_r);
        // cavity
        translate([wall, wall, floor_t]) rounded_box(inner_w, inner_h, tray_height, corner_r - wall + 0.1);
        left_cutouts();
        side_vents();
        feet_pockets();
        // latch groove inside the front wall's rebate
        translate([wall + 15, outer_h - wall + fit - latch_bump_d / 2 + 0.2, tray_height - lid_lip + 1.2])
            rotate([0, 90, 0]) cylinder(d = latch_bump_d + 0.3, h = inner_w - 30);
        // lid seat: a rebate around the top inside edge
        translate([wall - fit, wall - fit, tray_height - lid_lip])
            difference() {
                rounded_box(inner_w + 2 * fit, inner_h + 2 * fit, lid_lip + 1, corner_r - wall + fit);
            }
    }
    standoffs();
    card_supports();
    difference() {
        for (k = tray_knuckles()) knuckle(k[0], k[1]);
        hinge_bore();
    }
}

// --------------------------------------------------------------- lid
// comb under the lid (C30): one rib in every gap between neighbouring cards, plus one in front of the last. Each rib stands
// comb_gap from the card's back face on one side and comb_gap from the next receptacle housing on the other, so the closed lid
// holds the cards upright. Window x is the receptacle centre; the card slab is card_off behind it, the housing 4.9 in front.
hous_front = 4.9;
slab_back  = card_off + card_t / 2;
rib_w      = 14.5 - hous_front - slab_back - 2 * comb_gap;   // slot pitch minus card and housing
module comb() {
    y0 = lby(comb_y[1]); len_y = comb_y[1] - comb_y[0];
    feature("slot")
        translate([bx($f[2] + slab_back + comb_gap), y0, lid_t - 0.01]) cube([rib_w, len_y, comb_depth]);
    translate([bx(slot_x_min - hous_front - comb_gap - rib_w), y0, lid_t - 0.01]) cube([rib_w, len_y, comb_depth]);
}

// lid artwork: octopus brain and the name, engraved into the outer face and read from above with the hinge at the top
module lid_artwork() {
    s = logo_mm / logo_w;
    translate([bx(logo_pos[0]), lby(logo_pos[1]), -0.01]) mirror([1, 0, 0]) linear_extrude(engrave_d + 0.01) {
        scale(s) logo2d();
        translate([0, -name_dy]) text(name_text, size = name_size, font = "DejaVu Sans:style=Bold", halign = "center", valign = "center");
        translate([0, -sub_dy]) text(sub_text, size = sub_size, font = "DejaVu Sans", halign = "center", valign = "center");
    }
}

module lid() {
    // modelled right way up with z = 0 at the lid's outer top; in the scene it is turned over onto the tray
    // (rotate 180 about x, translate [0, outer_h, tray_height + lid_t]), so lid-local y = outer_h - tray y.
    difference() {
        union() {
            rounded_box(outer_w, outer_h, lid_t, corner_r);
            // skirt on the front and the two sides (lid-local y = 0 is the tray FRONT); the rear is the hinge
            translate([wall - fit, wall - fit, lid_t - 0.01])
                difference() {
                    rounded_box(inner_w + 2 * fit - 0.2, inner_h + 2 * fit - 0.2, lid_lip, corner_r - wall);
                    translate([wall, wall, -1]) rounded_box(inner_w - 2 * wall + 2 * fit, inner_h - 2 * wall + 2 * fit, lid_lip + 2, 1);
                    translate([-1, inner_h + 2 * fit - 0.2 - wall - 1, -1]) cube([outer_w, wall + 3, lid_lip + 2]);   // no rear skirt
                }
            comb();
            // latch bump along the front skirt's outer face
            translate([wall + 15, wall - fit - latch_bump_d / 2 + 0.2, lid_t + lid_lip - 1.2]) rotate([0, 90, 0]) cylinder(d = latch_bump_d, h = inner_w - 30);
            // hinge knuckles on the rear edge (lid-local y = outer_h), between the tray's
            for (x0 = [outer_w * 0.25 - 0.0, outer_w * 0.75 - hinge_knuckle_l])
                translate([x0 + 0.3, outer_h + hinge_knuckle_d / 2, lid_t]) {
                    rotate([0, 90, 0]) cylinder(d = hinge_knuckle_d, h = hinge_knuckle_l - 0.6);
                    translate([0, -hinge_knuckle_d / 2 - wall, -lid_t]) cube([hinge_knuckle_l - 0.6, hinge_knuckle_d / 2 + wall, lid_t]);
                }
        }
        translate([-1, outer_h + hinge_knuckle_d / 2, lid_t]) rotate([0, 90, 0]) cylinder(d = hinge_pin_d + 0.3, h = outer_w + 2);   // pin bore
        // OLED window and module recess: at oled_pos, or above J41 when oled_pos is empty
        feature("top") if ($f[0] == "J41") let (x = len(oled_pos) ? bx(oled_pos[0]) : bx($f[2]), y = len(oled_pos) ? lby(oled_pos[1]) : lby($f[3]) + 5) {
            translate([x - oled_win[0] / 2, y - oled_win[1] / 2, -1]) cube([oled_win[0], oled_win[1], lid_t + 2]);
            translate([x - oled_pcb[0] / 2, y - oled_pcb[1] / 2, lid_t - 1.2]) cube([oled_pcb[0], oled_pcb[1], 5]);
        }
        // bay slot windows: the cards' SATA receptacles poke through the lid (plug 28 x 9 mm on the card top)
        feature("slot") let (x = bx($f[2]), y = lby($f[3]), w = $f[5] + 2 * cut_clear, h = $f[6] + 2 * cut_clear)
            translate([x - w / 2, y - h / 2, -1]) cube([w, h, lid_t + 2]);
        lid_artwork();
        // DIP switch slot
        feature("top") if ($f[0] == "SW1") let (x = bx($f[2]), y = lby($f[3]), r = $f[4],
                                                 w = (r == 90 || r == 270) ? $f[6] : $f[5], h = (r == 90 || r == 270) ? $f[5] : $f[6])
            translate([x - (w + 2 * cut_clear) / 2, y - (h + 2 * cut_clear) / 2, -1]) cube([w + 2 * cut_clear, h + 2 * cut_clear, lid_t + 2]);
        // LED holes
        feature("led") translate([bx($f[2]), lby($f[3]), -1]) cylinder(d = $f[5], h = lid_t + 2);
        // convection grille over the CM5 cooler (board.scad gives the module centre)
        feature("cm5") let (cx = bx($f[2]), cy = lby($f[3]))
            translate([cx, cy, -1]) for (i = [0 : 8]) for (j = [0 : 8])
                let (px = (i - 4) * 4.5, py = (j - 4) * 4.5) if (px * px + py * py < (fan_grille_d / 2) * (fan_grille_d / 2))
                    translate([px, py, 0]) cylinder(d = 3, h = lid_t + 2);
    }
}

// --------------------------------------------------------------- output
if (part == "tray" || part == "all") tray();
if (part == "lid") lid();
if (part == "all") translate([0, outer_h + 15, 0]) lid();
