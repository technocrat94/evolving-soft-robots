"""All physical, controller, rendering and demonstration parameters (SI units)."""
DT = 0.002
SIM_SECONDS = 5.0
MASS = 0.1  # kg per shared corner node
GRAVITY = 9.81
STIFFNESS = {1: 1800.0, 2: 250.0, 3: 500.0, 4: 500.0}
SPRING_DAMPING = 6.0  # N s/m, relative axial velocity only
CONTACT_SPRING_DAMPING = 4.0  # extra axial damping in springs touching the floor
CONTACT_TOLERANCE = 1e-9  # m, numerical contact threshold (no adhesive contact)
POPULATION_SIZE = 60
GENERATIONS = 40
FRICTION = 0.9  # Coulomb coefficient; contact impulse limited by normal impulse
AMPLITUDE = 0.2
OMEGA = 3.0  # rad/s
START_HEIGHT = 0.02
MAX_POSITION = 10000.0
MAX_BODY_SIZE = 5
RANDOM_SEED = 42
FPS = 25
IMAGE_SIZE = (720, 550)
CAMERA_WIDTH = 10.0
COLORS = {1: '#444444', 2: '#bbbbbb', 3: '#f39c35', 4: '#88ccee'}
DEMO_BODY = [[3, 1, 3], [4, 2, 4], [4, 0, 4], [3, 0, 3]]
DEMO_PHASES = [[0.0, 0.0, 3.14], [1.57, 0.0, 4.71],
               [1.57, 0.0, 4.71], [0.0, 0.0, 3.14]]

# Genetic algorithm. Small-test CLI overrides do not change full-run defaults.
OMEGA_MIN = 1.0
OMEGA_MAX = 6.0
MUTATION_RATE = 0.08
ELITE_FRACTION = 0.20
TOURNAMENT_SIZE = 3
PHASE_MUTATION_STD = 0.25  # radians
OMEGA_MUTATION_STD = 0.35  # radians/s
INITIAL_MATERIAL_PROBABILITIES = (0.30, 0.15, 0.15, 0.20, 0.20)
MAX_INITIALIZATION_ATTEMPTS = 10000
MAX_CHILD_RETRIES = 50
WORKERS = None  # None uses every CPU core available to this process
PREVIEW_INTERVAL = 5
SMALL_POPULATION_SIZE = 10
SMALL_GENERATIONS = 5
RUN_UTC_OFFSET_HOURS = 8  # Taipei, used in result directory timestamps

# Reject sustained toppling; eligible fitness remains signed COM displacement.
FALL_ANGLE_DEGREES = 30.0
FALL_DURATION = 0.20  # seconds continuously beyond the tilt threshold
POSTURE_CHECK_INTERVAL = 10  # physics steps (0.02 s)

# Step 3 presentation settings (all panels share a physical scale).
COMPARISON_GENERATIONS = (1, 30, 60)
TIMELINE_GENERATIONS = (1, 10, 20, 30, 40, 50, 60)
COMPARISON_PANEL_SIZE = (480, 540)
COMPARISON_GROUND_MARGIN = 65
COMPARISON_HEADER_HEIGHT = 100
COMPARISON_MIN_VIEW_HEIGHT = 7.0
PLOT_DPI = 160
MATERIAL_NAMES = {1: 'Rigid', 2: 'Soft', 3: 'Horizontal actuator', 4: 'Vertical actuator'}

# Upgrade A: matched-seed ablation study; original 100x60 assets are unchanged.
EXPERIMENT_SEEDS = (42, 43, 44, 45, 46)
EXPERIMENT_CONDITIONS = ('co_evolution', 'body_only', 'control_only')
FIXED_OMEGA = 3.0
STATISTICAL_ALPHA = 0.05

# Upgrade B: seven sensors, eight hidden units, one output per actuator voxel.
CONTROL_INTERVAL = 10
NN_INPUTS = 7
NN_HIDDEN = 8
NN_INITIAL_STD = 0.5
NN_MUTATION_STD = 0.15
ROUGH_SEED = 2026
ROUGH_SPACING = 0.5
ROUGH_START = -20.0
ROUGH_END = 100.0
ROUGH_HEIGHT = 0.12
PUSH_TIME = 2.5
PUSH_DELTA_V = -1.5  # uniform backward velocity impulse (m/s)
ROBUSTNESS_SEEDS = (42, 43, 44, 45, 46)
ROBUSTNESS_TRAINING = 'flat'
