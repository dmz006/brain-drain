// brain-drain enclosure v1 ("brain box", C21): tray (bottom), lid (top), M.2 slot door.
// Board origin: x from the left, y from the REAR edge (the four drive cables), z from the
// board top surface. Left wall: DIN power, RJ45, USB-C. Front wall: microSD, M.2 SSD slot.
// Lid: OLED window, DIP slot, LED holes, fan grille. Right wall: vents only.
//   openscad -D part=\"tray\" -o stl/tray.stl shell.scad
//   openscad -D part=\"lid\"  -o stl/lid.stl  shell.scad
//   openscad -D part=\"door\" -o stl/door.stl shell.scad
include <params.scad>
use <refinements.scad>

part = "all";   // all | tray | lid | door
hinge = true;   // tray-side knuckles for the hinged door   // all | tray | lid | door
$fn = 48;

// --------------------------------------------------------------- helpers
// board coordinates -> enclosure coordinates. The rear edge (board y = 0) is the
// enclosure's -y wall; z = 0 is the tray floor's underside.
z_board_top = floor_t + below_board + board_t;
function bx(x) = wall + clear + x;
function by(y) = wall + clear + y;

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

module front_cutouts() {
    feature("front") let (x = bx($f[2]), w = $f[5] + 2 * cut_clear, h = $f[6] + 2 * cut_clear, z = $f[7])
        translate([x - w / 2, outer_h - wall - 1, z_board_top + z - cut_clear])
            cube([w, wall + 2, h]);
}

module door_cutout() {
    // front wall slot for the M.2 SSD: centred on the M.2 column's x, from the board up
    feature("m2") let (x = bx($f[2]))
        translate([x - door_w / 2, outer_h - wall - 1, z_board_top + door_z])
            cube([door_w, wall + 2, door_h]);
}

module buzzer_holes() {
    // ring of sound holes in the floor under the bottom-side buzzer
    feature("bottom") let (x = bx($f[2]), y = by($f[3]))
        for (a = [0 : 60 : 300]) translate([x + 3 * cos(a), y + 3 * sin(a), -1]) cylinder(d = 1.6, h = floor_t + 2);
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
    // vent slots in the RIGHT wall (x = outer_w), the only wall with nothing on it; the lid has the fan grille
    n = floor((inner_h - 30) / vent_pitch);
    for (i = [0 : n - 1])
        translate([outer_w - wall - 1, wall + 15 + i * vent_pitch, z_board_top + 6])
            cube([wall + 2, vent_w, above_board - 12]);
}

// --------------------------------------------------------------- tray
module tray() {
    difference() {
        rounded_box(outer_w, outer_h, tray_height, corner_r);
        // cavity
        translate([wall, wall, floor_t]) rounded_box(inner_w, inner_h, tray_height, corner_r - wall + 0.1);
        rear_cutouts();
        left_cutouts();
        front_cutouts();
        door_cutout();
        side_vents();
        buzzer_holes();
        feet_pockets();
        // lid seat: a rebate around the top inside edge
        translate([wall - fit, wall - fit, tray_height - lid_lip])
            difference() {
                rounded_box(inner_w + 2 * fit, inner_h + 2 * fit, lid_lip + 1, corner_r - wall + fit);
            }
    }
    standoffs();
    if (hinge) feature("m2") door_knuckles(bx($f[2]), z_board_top + door_z + door_h + door_lip);
    // lid screw bosses in the four corners (lid screws come down into these)
    for (c = [[wall + 3, wall + 3], [outer_w - wall - 3, wall + 3], [wall + 3, outer_h - wall - 3], [outer_w - wall - 3, outer_h - wall - 3]])
        translate([c[0], c[1], floor_t]) difference() {
            cylinder(d = 6, h = tray_height - floor_t - lid_lip);
            translate([0, 0, tray_height - floor_t - lid_lip - insert_h]) cylinder(d = insert_d, h = insert_h + 1);
        }
}

// --------------------------------------------------------------- lid
module lid() {
    // printed upside down; modelled right way up with z = 0 at the lid's outer top
    difference() {
        union() {
            rounded_box(outer_w, outer_h, lid_t, corner_r);
            // skirt that drops into the tray rebate
            translate([wall - fit, wall - fit, lid_t - 0.01])
                difference() {
                    rounded_box(inner_w + 2 * fit - 0.2, inner_h + 2 * fit - 0.2, lid_lip, corner_r - wall);
                    translate([wall, wall, -1]) rounded_box(inner_w - 2 * wall + 2 * fit, inner_h - 2 * wall + 2 * fit, lid_lip + 2, 1);
                }
        }
        // OLED window and module recess: at oled_pos, or above J41 when oled_pos is empty
        feature("top") if ($f[0] == "J41") let (x = len(oled_pos) ? bx(oled_pos[0]) : bx($f[2]), y = len(oled_pos) ? by(oled_pos[1]) : by($f[3]) - 5) {
            translate([x - oled_win[0] / 2, y - oled_win[1] / 2, -1]) cube([oled_win[0], oled_win[1], lid_t + 2]);
            translate([x - oled_pcb[0] / 2, y - oled_pcb[1] / 2, lid_t - 1.2]) cube([oled_pcb[0], oled_pcb[1], 5]);
        }
        // DIP switch slot
        feature("top") if ($f[0] == "SW1") let (x = bx($f[2]), y = by($f[3]), r = $f[4],
                                                 w = (r == 90 || r == 270) ? $f[6] : $f[5], h = (r == 90 || r == 270) ? $f[5] : $f[6])
            translate([x - (w + 2 * cut_clear) / 2, y - (h + 2 * cut_clear) / 2, -1]) cube([w + 2 * cut_clear, h + 2 * cut_clear, lid_t + 2]);
        // LED holes
        feature("led") translate([bx($f[2]), by($f[3]), -1]) cylinder(d = $f[5], h = lid_t + 2);
        // fan grille over the CM5 (board.scad gives the module centre)
        feature("cm5") let (cx = bx($f[2]), cy = by($f[3]))
            translate([cx, cy, -1]) for (i = [0 : 8]) for (j = [0 : 8])
                let (px = (i - 4) * 4.5, py = (j - 4) * 4.5) if (px * px + py * py < (fan_grille_d / 2) * (fan_grille_d / 2))
                    translate([px, py, 0]) cylinder(d = 3, h = lid_t + 2);
        // corner screw holes
        for (c = [[wall + 3, wall + 3], [outer_w - wall - 3, wall + 3], [wall + 3, outer_h - wall - 3], [outer_w - wall - 3, outer_h - wall - 3]])
            translate([c[0], c[1], -1]) cylinder(d = screw_d, h = lid_t + lid_lip + 2);
    }
}

// --------------------------------------------------------------- door plug
module door() {
    // snap-in blank for the M.2 opening; replace with a hinged door later
    cube([door_plug_t, door_w - 2 * fit, door_h - 2 * fit]);
    translate([door_plug_t, 2, 2]) cube([1.2, door_w - 2 * fit - 4, door_h - 2 * fit - 4]);
}

// --------------------------------------------------------------- output
if (part == "tray" || part == "all") tray();
if (part == "lid") lid();
if (part == "all") translate([0, outer_h + 15, 0]) lid();
if (part == "door") door();
if (part == "all") translate([outer_w + 15, 0, 0]) door();
