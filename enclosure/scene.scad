// Assembled-unit scene for renders: enclosure with lid, four 3.5" drives on the rack,
// pigtails from the rear SATA receptacles, power and network cables.
//   openscad -D group=\"unit\"   -o stl/scene_unit.stl   scene.scad
//   openscad -D group=\"drives\" -o stl/scene_drives.stl scene.scad
//   openscad -D group=\"cables\" -o stl/scene_cables.stl scene.scad
include <params.scad>
use <shell.scad>
use <refinements.scad>
group = "all";
$fn = 32;

drive = [147, 101.6, 26.1];          // 3.5" HDD
rack_y = -(rack_depth + 60);         // rack sits behind the unit (cables leave the rear = -y side)

module unit() {
    tray();
    translate([0, outer_h, tray_height + lid_t]) rotate([180, 0, 0]) lid();   // lid turned over onto the tray (rotation keeps face normals outward)
}

module drives() {
    translate([outer_w / 2 - (rack_slots * rack_pitch + rack_wall) / 2, rack_y, 0]) {
        rack();
        for (i = [0 : rack_slots - 1])
            translate([i * rack_pitch + rack_wall + (rack_slot_w - drive[2]) / 2, -60, rack_wall])
                cube([drive[2], drive[0], drive[1]]);   // drive standing on its long edge, connector end toward the unit
    }
}

// a cable is a swept bezier: hull of small spheres along the curve
module cable(p0, p1, p2, p3, d = 6) {
    n = 24;
    for (i = [0 : n - 1]) {
        t0 = i / n; t1 = (i + 1) / n;
        hull() {
            translate(bez(p0, p1, p2, p3, t0)) sphere(d = d);
            translate(bez(p0, p1, p2, p3, t1)) sphere(d = d);
        }
    }
}
function bez(p0, p1, p2, p3, t) = p0 * pow(1 - t, 3) + p1 * 3 * t * pow(1 - t, 2) + p2 * 3 * t * t * (1 - t) + p3 * pow(t, 3);

module cables() {
    zc = floor_t + below_board + board_t + 5;           // SATA plug height above the floor
    // four SATA pigtails from the receptacle positions to the drives' connector ends
    for (f = board_features) if (f[1] == "rear" && (f[0] == "J10" || f[0] == "J11" || f[0] == "J12" || f[0] == "J13"))
        let (i = f[0] == "J10" ? 0 : f[0] == "J11" ? 1 : f[0] == "J12" ? 2 : 3,
             x0 = wall + clear + f[2], dx = outer_w / 2 - (rack_slots * rack_pitch + rack_wall) / 2 + i * rack_pitch + rack_wall + rack_slot_w / 2,
             p0 = [x0, 0, zc], p3 = [dx, rack_y + rack_depth - 60 + 2, rack_wall + 20])
            cable(p0, [x0, -40, zc + 10], [dx, rack_y + 90, 25], p3, 9);
    // power (DIN) and network cables trailing off to -y
    for (f = board_features) if (f[0] == "J21") let (x0 = wall + clear + f[2]) cable([x0, 0, zc + 4], [x0 - 10, -60, 30], [x0 - 40, -160, 10], [x0 - 60, -260, 4], 7);
    for (f = board_features) if (f[0] == "J4") let (x0 = wall + clear + f[2]) cable([x0, 0, zc + 4], [x0 + 5, -70, 25], [x0 + 20, -180, 8], [x0 + 30, -280, 4], 5);
}

if (group == "unit" || group == "all") unit();
if (group == "drives" || group == "all") drives();
if (group == "cables" || group == "all") cables();
