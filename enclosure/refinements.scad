// brain-drain enclosure refinements: hinged M.2 door, OLED bezel, feet, drive rack.
//   openscad -D part=\"door_hinged\" -o stl/door_hinged.stl refinements.scad
//   openscad -D part=\"bezel\"       -o stl/bezel.stl       refinements.scad
//   openscad -D part=\"rack\"        -o stl/rack.stl        refinements.scad
include <params.scad>
part = "all";
$fn = 48;

// ------------------------------------------------ hinged door (right wall)
// Two knuckles on the tray side are added by shell.scad when hinge=true; this is the
// leaf: a plate with a lip that overlaps the opening, one centre knuckle, filament pin.
module door_hinged() {
    w = door_w + 2 * door_lip;
    h = door_h + 2 * door_lip;
    difference() {
        union() {
            cube([door_plug_t, w, h]);                                     // leaf
            translate([door_plug_t, door_lip + fit, door_lip + fit])       // plug that enters the opening
                cube([wall - 0.4, door_w - 2 * fit, door_h - 2 * fit]);
            translate([0, w / 2 - 6, h]) rotate([0, 90, 0])                // centre knuckle on the top edge
                translate([-hinge_knuckle_d / 2, 0, 0]) cube([hinge_knuckle_d, 12, door_plug_t]);
            translate([door_plug_t / 2, w / 2 - 6, h + hinge_knuckle_d / 2 - 0.01]) rotate([-90, 0, 0])
                cylinder(d = hinge_knuckle_d, h = 12);
        }
        translate([door_plug_t / 2, w / 2 - 8, h + hinge_knuckle_d / 2]) rotate([-90, 0, 0])
            cylinder(d = hinge_pin_d + 0.3, h = 16);                       // pin bore
        // finger notch
        translate([-1, w / 2 - 5, -1]) cube([door_plug_t + 2, 10, 2.5]);
    }
}

// tray-side knuckles: call from shell.scad's tray() at the door position
module door_knuckles(y_centre, z_top) {
    for (dy = [-14, 8])
        translate([outer_w - wall - 0.01, y_centre + dy, z_top + hinge_knuckle_d / 2])
            difference() {
                union() {
                    rotate([-90, 0, 0]) cylinder(d = hinge_knuckle_d, h = 6);
                    translate([-wall + 0.01, 0, -hinge_knuckle_d / 2]) cube([wall, 6, hinge_knuckle_d]);
                }
                translate([0, -1, 0]) rotate([-90, 0, 0]) cylinder(d = hinge_pin_d + 0.3, h = 8);
            }
}

// ------------------------------------------------ OLED bezel (clamps the module under the lid window)
module bezel() {
    pw = oled_pcb[0] + 4; ph = oled_pcb[1] + 4;
    difference() {
        union() {
            translate([-pw / 2, -ph / 2, 0]) cube([pw, ph, bezel_t]);
            for (sx = [-1, 1]) for (sy = [-1, 1])
                translate([sx * oled_hole_pitch[0] / 2, sy * oled_hole_pitch[1] / 2, bezel_t - 0.01])
                    cylinder(d = bezel_post_d, h = bezel_post_h);
        }
        for (sx = [-1, 1]) for (sy = [-1, 1])
            translate([sx * oled_hole_pitch[0] / 2, sy * oled_hole_pitch[1] / 2, -1])
                cylinder(d = 1.8, h = bezel_t + bezel_post_h + 2);        // M2 self-tap
        translate([-oled_win[0] / 2 - 1, -oled_win[1] / 2 - 1 - 5, -1]) cube([oled_win[0] + 2, oled_win[1] + 2, bezel_t + 2]);
        // pin header clearance (4-pin at the module's top edge)
        translate([-6, oled_pcb[1] / 2 - 4, -1]) cube([12, 4, bezel_t + 2]);
    }
}

// ------------------------------------------------ feet: pockets in the tray underside
module feet_pockets() {
    for (c = [[feet_inset, feet_inset], [outer_w - feet_inset, feet_inset], [feet_inset, outer_h - feet_inset], [outer_w - feet_inset, outer_h - feet_inset]])
        translate([c[0], c[1], -1]) cylinder(d = feet_d, h = feet_depth + 1);
}

// ------------------------------------------------ drive rack
module rack() {
    w = rack_slots * rack_pitch + rack_wall;
    difference() {
        // base with a raised back stop
        union() {
            cube([w, rack_depth, rack_wall]);
            translate([0, rack_depth - rack_wall, 0]) cube([w, rack_wall, rack_height]);
            for (i = [0 : rack_slots]) translate([i * rack_pitch, 0, 0]) cube([rack_wall, rack_depth, rack_height]);
        }
        for (i = [0 : rack_slots - 1]) let (x0 = i * rack_pitch + rack_wall) {
            // 2.5" groove in the floor of each slot, centred
            translate([x0 + (rack_slot_w - rack_25_w) / 2 - 0.5, -1, rack_wall - 1.2]) cube([rack_25_w + 1, rack_depth - rack_wall + 1, 2]);
            // pigtail notch in the back stop
            translate([x0 + rack_slot_w / 2 - 12, rack_depth - rack_wall - 1, rack_height - 14]) cube([24, rack_wall + 2, 15]);
        }
        // ventilation slots in the floor
        for (i = [0 : rack_slots - 1]) for (k = [0 : 2])
            translate([i * rack_pitch + rack_wall + 4 + k * 7, 6, -1]) cube([3, rack_depth - 20, rack_wall + 2]);
        // feet pockets
        for (c = [[6, 6], [w - 6, 6], [6, rack_depth - 6], [w - 6, rack_depth - 6]]) translate([c[0], c[1], -1]) cylinder(d = feet_d, h = feet_depth + 1);
    }
}

if (part == "door_hinged" || part == "all") door_hinged();
if (part == "bezel") bezel();
if (part == "all") translate([30, 0, 0]) bezel();
if (part == "rack") rack();
if (part == "all") translate([0, 40, 0]) rack();
