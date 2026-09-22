// Assembled scene for the renders (C21, portable use): the closed unit, four loose drives lying
// on the bench behind it, a 22-pin cable from each rear receptacle to its drive, and the power
// and network cables leaving the left wall.
//   openscad -D group=\"unit\"   -o stl/scene_unit.stl   scene.scad
//   openscad -D group=\"drives\" -o stl/scene_drives.stl scene.scad
//   openscad -D group=\"cables\" -o stl/scene_cables.stl scene.scad
include <params.scad>
use <shell.scad>
use <refinements.scad>
group = "all";
$fn = 32;

drive35 = [101.6, 147, 26.1];       // 3.5" HDD lying flat, connector on the face toward the unit (+y)
drive25 = [69.85, 100, 9.5];        // 2.5" HDD/SSD
drive_gap = 60;                      // between the unit's rear wall and the drives' connector faces
drive_pitch = 118;
drives_x0 = outer_w / 2 - 1.5 * drive_pitch;   // four drives centred on the unit

function drive_size(i) = (i == 3) ? drive25 : drive35;
function drive_cx(i) = drives_x0 + i * drive_pitch;
function drive_front(i) = -drive_gap;   // y of the connector face (unit rear wall is y = 0)

module unit() {
    tray();
    translate([0, outer_h, tray_height + lid_t]) rotate([180, 0, 0]) lid();   // lid turned over onto the tray
}

module drives() {
    for (i = [0 : 3]) let (d = drive_size(i))
        translate([drive_cx(i) - d[0] / 2, drive_front(i) - d[1], 0]) cube(d);
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
    zc = floor_t + below_board + board_t + 5;           // SATA plug height above the bench
    // four 22-pin cables from the receptacles to the drives' connector faces (cable enters the drive low, near the bench)
    for (f = board_features) if (f[1] == "rear" && (f[0] == "J10" || f[0] == "J11" || f[0] == "J12" || f[0] == "J13"))
        let (i = f[0] == "J10" ? 0 : f[0] == "J11" ? 1 : f[0] == "J12" ? 2 : 3,
             x0 = wall + clear + f[2], dx = drive_cx(i) + 12, zd = drive_size(i)[2] / 2,
             p0 = [x0, 0, zc], p3 = [dx, drive_front(i) + 1, zd])
            cable(p0, [x0, -25, zc + 6], [dx, drive_front(i) + 30, zd + 4], p3, 9);
    // power (DIN) and network cables leave the LEFT wall and trail off to -x
    for (f = board_features) if (f[0] == "J21") let (y0 = wall + clear + f[3]) cable([0, y0, zc + 4], [-40, y0 - 10, 25], [-140, y0 - 60, 10], [-240, y0 - 120, 4], 7);
    for (f = board_features) if (f[0] == "J4") let (y0 = wall + clear + f[3]) cable([0, y0, zc + 4], [-45, y0 + 10, 22], [-150, y0 + 60, 8], [-250, y0 + 120, 4], 5);
}

if (group == "unit" || group == "all") unit();
if (group == "drives" || group == "all") drives();
if (group == "cables" || group == "all") cables();
