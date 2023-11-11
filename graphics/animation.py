import numpy as np
import pygame
import random

# ~ Camera effects
def ease_in_out(t):
    if t < 0.5: return 4 * t * t * t
    else:
        f = ((2 * t) - 2)
        return 0.5 * f * f * f + 1

def add_shake(position, progress, max_intensity):
    # Interpolate the shake intensity based on progress
    shake_intensity = ease_in_out(progress) * max_intensity
    shake = np.random.uniform(-shake_intensity, shake_intensity, size=position.shape)
    shake[1] = 0  # No shake on the y-axis
    return position + shake

# ~ Camera animation
def build_intro_camera_animations(yaw, pitch, camera_distance): return {
    "1": [ # "Grand Entrance"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 10, "time": 0},  # Start from top-down
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(45), "distance": 5, "time": 3},  # Spin around above the board
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(30), "distance": 3, "time": 5},  # Move to a lower side-view
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 8}  # Ease to starting point
    ],
    "2": [ # "Orbit Descend"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 12, "time": 0},  # Start from high top-down
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(60), "distance": 6, "time": 4},  # Descend halfway around the board
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(30), "distance": 4, "time": 7},  # Complete the orbit closer
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 10}  # Ease to starting point
    ],
    "3": [ # "Aerial Spiral"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 15, "time": 0},  # Start from very high top-down
        {"yaw": np.deg2rad(90), "pitch": np.deg2rad(80), "distance": 8, "time": 2},  # Quick descent to side
        {"yaw": np.deg2rad(270), "pitch": np.deg2rad(80), "distance": 8, "time": 4},  # Continue orbit at same elevation
        {"yaw": np.deg2rad(450), "pitch": np.deg2rad(80), "distance": 8, "time": 6},  # Complete the orbit
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 9}  # Ease to starting point
    ],
    "4": [ # "Hovering Glide"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 10, "time": 0},  # Start from top-down
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(45), "distance": 5, "time": 3},  # Half orbit to side-view
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(10), "distance": 5, "time": 5},  # Lower the pitch for a flatter view
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(10), "distance": 5, "time": 7},  # Complete the orbit at flatter angle
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 9}  # Ease to starting point
    ],
    "5": [ # "Double Helix"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 15, "time": 0},  # Start from high top-down
        {"yaw": np.deg2rad(720), "pitch": np.deg2rad(45), "distance": 5, "time": 5},  # Double spin around the board
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 8}  # Ease to starting point
    ],
    "6": [ # "Vertical Dive"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 10, "time": 0},  # Start from top-down
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(90), "distance": 10, "time": 2},  # Descend to a vertical side-view
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(45), "distance": 3, "time": 4},  # Lower the pitch for a closer view
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(45), "distance": 3, "time": 6},  # Orbit around the board at angle
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 8}  # Ease to starting point
    ],
    "7": [ # "Elevated Carousel"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 12, "time": 0},  # Start from high top-down
        {"yaw": np.deg2rad(90), "pitch": np.deg2rad(60), "distance": 7, "time": 3},  # Descend to a high side-view
        {"yaw": np.deg2rad(270), "pitch": np.deg2rad(60), "distance": 7, "time": 5},  # Continue orbit at same elevation
        {"yaw": np.deg2rad(450), "pitch": np.deg2rad(60), "distance": 7, "time": 7},  # Complete the orbit
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 9}  # Ease to starting point
    ],
    "8": [ # "Sky Dancer"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 14, "time": 0},  # Start from very high top-down
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(70), "distance": 6, "time": 3},  # Half orbit to a high side-view
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(70), "distance": 6, "time": 5},  # Complete the orbit at same elevation
        {"yaw": np.deg2rad(540), "pitch": np.deg2rad(70), "distance": 6, "time": 7},  # Continue spinning around
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 10}  # Ease to starting point
    ],
    "9": [ # "Serene Orbit"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 12, "time": 0},  # Start from high top-down
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(45), "distance": 8, "time": 3},  # Begin orbit descent
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(30), "distance": 7, "time": 5},  # Continue gentle orbit
        {"yaw": np.deg2rad(540), "pitch": np.deg2rad(20), "distance": 7, "time": 7},  # Further orbit with lower pitch
        {"yaw": np.deg2rad(720), "pitch": np.deg2rad(10), "distance": 7, "time": 9},  # Complete the serene orbit
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 11}  # Ease to starting point
    ],
    "10": [ # "Celestial Glide"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 14, "time": 0},  # Start from a lofty top-down
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(80), "distance": 6, "time": 4},  # Steady descent in a wide orbit
        {"yaw": np.deg2rad(720), "pitch": np.deg2rad(40), "distance": 4, "time": 8},  # Continue orbiting at lower altitude
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 12}  # Glide into the starting position
    ],
    "11": [ # "Panoramic Spiral"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 13, "time": 0},  # Begin from an expansive top-down
        {"yaw": np.deg2rad(540), "pitch": np.deg2rad(60), "distance": 9, "time": 4},  # Spiral down in a panoramic orbit
        {"yaw": np.deg2rad(1080), "pitch": np.deg2rad(20), "distance": 5, "time": 8},  # Continue the spiral closer to the board
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 12}  # Smoothly transition to the game view
    ],
    "12": [ # "Orbiting Observer"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 11, "time": 0},  # Start with a broad view from above
        {"yaw": np.deg2rad(270), "pitch": np.deg2rad(70), "distance": 7, "time": 3},  # Begin a high-altitude orbit
        {"yaw": np.deg2rad(540), "pitch": np.deg2rad(50), "distance": 7, "time": 6},  # Maintain orbit with a slight descent
        {"yaw": np.deg2rad(810), "pitch": np.deg2rad(30), "distance": 7, "time": 9},  # Continue orbiting with a gradual approach
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 12}  # Conclude with a smooth transition to start
    ],
    "13": [  # "Swift Approach"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 12, "time": 0}, # Start high and distant for a full view
        {"yaw": np.deg2rad(60), "pitch": np.deg2rad(45), "distance": 9, "time": 1}, # Begin descent with a slight turn
        {"yaw": np.deg2rad(120), "pitch": np.deg2rad(45), "distance": 6, "time": 2}, # Continue turning, coming in closer
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(30), "distance": 4, "time": 3}, # Halfway through the orbit, lower the camera
        {"yaw": np.deg2rad(240), "pitch": np.deg2rad(30), "distance": 3, "time": 4}, # Start to level out the pitch as we near the board
        {"yaw": np.deg2rad(300), "pitch": np.deg2rad(15), "distance": 2, "time": 5}, # Final approach, almost level with the board
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 6}, # Ease into the starting position
    ],
    "14": [  # "Rapid Orbit"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 14, "time": 0},
        {"yaw": np.deg2rad(90), "pitch": np.deg2rad(60), "distance": 11, "time": 1},
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(60), "distance": 8, "time": 2},
        {"yaw": np.deg2rad(270), "pitch": np.deg2rad(45), "distance": 5, "time": 3},
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(45), "distance": 3, "time": 4},
        {"yaw": np.deg2rad(450), "pitch": np.deg2rad(30), "distance": 2, "time": 5},
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 6},
    ],
    "15": [  # "Descending Spiral"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 13, "time": 0},
        {"yaw": np.deg2rad(120), "pitch": np.deg2rad(75), "distance": 10, "time": 1},
        {"yaw": np.deg2rad(240), "pitch": np.deg2rad(50), "distance": 7, "time": 2},
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(50), "distance": 5, "time": 3},
        {"yaw": np.deg2rad(480), "pitch": np.deg2rad(25), "distance": 4, "time": 4},
        {"yaw": np.deg2rad(600), "pitch": np.deg2rad(25), "distance": 3, "time": 5},
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 6},
    ],
    "16": [  # "Glide and Slide"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 15, "time": 0},
        {"yaw": np.deg2rad(70), "pitch": np.deg2rad(65), "distance": 12, "time": 1},
        {"yaw": np.deg2rad(140), "pitch": np.deg2rad(65), "distance": 9, "time": 2},
        {"yaw": np.deg2rad(210), "pitch": np.deg2rad(40), "distance": 6, "time": 3},
        {"yaw": np.deg2rad(280), "pitch": np.deg2rad(40), "distance": 4, "time": 4},
        {"yaw": np.deg2rad(350), "pitch": np.deg2rad(20), "distance": 3, "time": 5},
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 6},
    ],
    "17": [  # "Hovering Advance"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 14, "time": 0},
        {"yaw": np.deg2rad(50), "pitch": np.deg2rad(70), "distance": 11, "time": 1},
        {"yaw": np.deg2rad(100), "pitch": np.deg2rad(70), "distance": 8, "time": 2},
        {"yaw": np.deg2rad(150), "pitch": np.deg2rad(45), "distance": 6, "time": 3},
        {"yaw": np.deg2rad(200), "pitch": np.deg2rad(45), "distance": 5, "time": 4},
        {"yaw": np.deg2rad(250), "pitch": np.deg2rad(20), "distance": 4, "time": 5},
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 6},
    ],
    "18": [  # "Circling Descent"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 16, "time": 0},
        {"yaw": np.deg2rad(30), "pitch": np.deg2rad(80), "distance": 13, "time": 1},
        {"yaw": np.deg2rad(60), "pitch": np.deg2rad(80), "distance": 10, "time": 2},
        {"yaw": np.deg2rad(90), "pitch": np.deg2rad(55), "distance": 8, "time": 3},
        {"yaw": np.deg2rad(120), "pitch": np.deg2rad(55), "distance": 6, "time": 4},
        {"yaw": np.deg2rad(150), "pitch": np.deg2rad(30), "distance": 5, "time": 5},
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 6},
    ],
    "19": [  # "The Grand Panorama"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(0), "distance": 16, "time": 0}, # Begin with a panoramic view from above
        {"yaw": np.deg2rad(30), "pitch": np.deg2rad(75), "distance": 14, "time": 0.5}, # Start the descent with a gentle turn
        {"yaw": np.deg2rad(60), "pitch": np.deg2rad(70), "distance": 12, "time": 1}, # Continue the descent, orbiting the board
        {"yaw": np.deg2rad(90), "pitch": np.deg2rad(65), "distance": 10, "time": 1.5}, # Lower the pitch slightly, coming in closer
        {"yaw": np.deg2rad(120), "pitch": np.deg2rad(60), "distance": 8, "time": 2}, # Keep the smooth descent with a steady turn
        {"yaw": np.deg2rad(150), "pitch": np.deg2rad(55), "distance": 7, "time": 2.5}, # Halfway through the orbit, lower the camera further
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(50), "distance": 6, "time": 3}, # Continue the orbit, preparing for a closer look
        {"yaw": np.deg2rad(210), "pitch": np.deg2rad(45), "distance": 5, "time": 3.5}, # Orbit closer to the board, lowering the pitch
        {"yaw": np.deg2rad(240), "pitch": np.deg2rad(40), "distance": 4, "time": 4}, # Close in on the board, maintaining a steady orbit
        {"yaw": np.deg2rad(270), "pitch": np.deg2rad(35), "distance": 3.5, "time": 4.5}, # Start to level out the pitch as we near the game
        {"yaw": np.deg2rad(300), "pitch": np.deg2rad(30), "distance": 3, "time": 5}, # Final approach, almost level with the board
        {"yaw": np.deg2rad(330), "pitch": np.deg2rad(25), "distance": 2.5, "time": 5.5}, # Ease into the starting position, ready for the game
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 6}, # Settle into the starting position
    ],
    "20": [  # "Butterfly Dance" (* BEST ONE *)
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(90), "distance": 14, "time": 0},  # High above, looking straight down
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(45), "distance": 7, "time": 2},  # Swoop down, half orbit to side view
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 4},  # Glide into the starting position
    ],
    "21": [  # "Silken Slide" (* SECOND BEST *)
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(10), "distance": 10, "time": 0},  # Start slightly elevated from the end position
        {"yaw": np.deg2rad(90), "pitch": np.deg2rad(20), "distance": 5, "time": 1.5},  # Smooth transition to a closer side view
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 3},  # Softly settle into the starting view
    ],
    "22": [  # "Velvet Orbit"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(30), "distance": 12, "time": 0},  # Begin with a gentle look from above
        {"yaw": np.deg2rad(270), "pitch": np.deg2rad(45), "distance": 6, "time": 2},  # Graceful wide orbit around the board
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 4},  # Ease into the final position
    ],
    "23": [  # "CCurve"
        {"yaw": np.deg2rad(1), "pitch": np.deg2rad(80), "distance": 15, "time": 0},  # High and distant, steep angle for drama
        {"yaw": np.deg2rad(180), "pitch": np.deg2rad(60), "distance": 8, "time": 2},  # Smooth descent into a closer orbit
        {"yaw": np.deg2rad(360), "pitch": np.deg2rad(40), "distance": 4, "time": 3.5},  # Continue the descent, circling the board
        {"yaw": yaw, "pitch": pitch, "distance": camera_distance, "time": 5},  # Round off into the starting position
    ],
}