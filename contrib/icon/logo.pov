/*
 * Bookkeeper Logo
 */

#include "colors.inc"
#include "shapes.inc"
#include "textures.inc"

#declare FrameColor = GreenYellow;
#declare hoz_x = 1.64;
#declare ver_x = 1.2;

#macro FlattenedSphere(bobbin_color, locale, slider)
   object {
      sphere { <0, 0, 0>, 0.075 }
      scale <1.4, 1.0, 1.4>
      pigment { bobbin_color }
      rotate <0, 0, 90>
      // local max=0.74, min=-0.74
      // slider top=0.28, middle=0.0, bottom=-0.28
      // The space taken up by a button is 0.14.
      translate <locale, slider, 0>
   }
#end

#macro RoundedEndSegment(x_cylinder, z_rotation, x_translate, y_translate)
   #declare Outer = cylinder { <x_cylinder, 0, 0>, <0, 0, 0>, 0.05 }
   #declare OuterEnd = sphere { <0, 0, 0>  0.05 }
   union {
      object {
         Outer
         pigment { FrameColor }
         rotate <0, 0, z_rotation>
         translate <-x_translate, -y_translate, 0>
      }

      object {
         OuterEnd
         pigment { FrameColor }
         translate <x_translate, y_translate, 0>
      }

      object {
         OuterEnd
         pigment { FrameColor }
         translate <-x_translate, -y_translate, 0>
      }
   }
#end

background {
   color Gray75
}

object {
   // RoundedEndSegment(x_cylinder, z_rotation, x_translate, y_translate)
   RoundedEndSegment(hoz_x, 0, 0.82, 0)
   translate <0, 0.6, 0>
}

object {
   // RoundedEndSegment(x_cylinder, z_rotation, x_translate, y_translate)
   RoundedEndSegment(hoz_x, 0, 0.82, 0)
   translate <0, -0.6, 0>
}

object {
   // RoundedEndSegment(x_cylinder, z_rotation, x_translate, y_translate)
   RoundedEndSegment(ver_x, 90, 0, 0.6)
   translate <-0.82, 0, 0>
}

object {
   // RoundedEndSegment(x_cylinder, z_rotation, x_translate, y_translate)
   RoundedEndSegment(ver_x, 90, 0, 0.6)
   translate <0.82, 0, 0>
}

#declare HorzSlider = object {
      cylinder { <hoz_x, 0, 0>, <0, 0, 0>, 0.03 }
      pigment { FrameColor }
      translate <-0.82, 0, 0>
}

union {
   #declare slider = 0.28;
   object {
      HorzSlider
      translate <0, slider, 0>
   }
   FlattenedSphere(BlueViolet, 0.60, slider)
   FlattenedSphere(BlueViolet, 0.18, slider)
   FlattenedSphere(BlueViolet, -0.28, slider)
}

union {
   #declare slider = 0;
   object {
      HorzSlider
      translate <0, slider, 0>
   }
   FlattenedSphere(OrangeRed, 0.74, slider)
   FlattenedSphere(OrangeRed, 0.46, slider)
   FlattenedSphere(OrangeRed, 0.18, slider)
}

union {
   #declare slider = -0.28;
   object {
      HorzSlider
      translate <0, slider, 0>
   }
   FlattenedSphere(NeonBlue, -0.00, slider)
   FlattenedSphere(NeonBlue, -0.28, slider)
   FlattenedSphere(NeonBlue, -0.46, slider)
}

light_source {
   <0, 0, -10>
   color White
}

light_source {
   <5, 0, 10>
   color White
}

camera {
   location <0, 0, 1.5> // Front View
   //location <-1.5, 0, 0.75>  // Left 45 degrees
   //location <-1.5, 0, -1.25>  // Left 45 degrees
   look_at <0, 0, 0>
}
