# Current-run correction

The initial success claim following the first lift and hold check was withdrawn.
The user observed that the farther bottom corner still touched the desk.
Stationary images and stable encoders alone did not establish full clearance.
The same attempt continues with a larger bounded lift and a fresh check of all
bottom corners. No skill update or commit had occurred before this correction.

The controller now preserves already enabled motors' goals on restart, including
gripper preload. Its fault hold preserves the gripper goal. Low-load, stationary
shortfalls are recorded separately from reaching the requested target.
