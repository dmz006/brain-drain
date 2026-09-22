// brain-drain enclosure refinements: OLED bezel, feet pockets.
//   openscad -D part=\"bezel\" -o stl/bezel.stl refinements.scad
include <params.scad>
part = "all";
$fn = 48;

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

if (part == "bezel" || part == "all") bezel();
