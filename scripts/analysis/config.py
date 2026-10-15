DATA_FILE = "Engine_WM_Year_ID_MSK.xlsx"

SHEET_COMBOS = "Engine&MSK"
SHEET_STUDIES = "Sheet1"
SHEET_TASKS = "Sheet2"
SHEET_ALGO = "Algo"

COL_ID = "ID"
COL_YEARS = "Years"
COL_ENGINE = "Physics Engine"
COL_MSK = "Musculoskeletal systems"
COL_LDM = "Learned Dynamics Model"
COL_COMP = "Competition origin"
COL_CLEARLY = "Clearly?"
COL_TASK_TYPE = "Task type"
COL_SUBCATEGORY = "Subcategory"
COL_DATAREF = "Data Reference"
COL_ALGO = "RL Algo."
COL_PIO_FLAG = "π input & output clearly reported"

DROP_IDS = [90, 91, 92]
PERIODS = ["2017–2019", "2020–2022", "2023–2025"]

REWARD_ATOMS = [
    "Imitation", "Coordination", "Joint activity suppression",
    "Postural stability", "Effort regularization", "Knee flexion bias",
    "Locomotion progress", "Velocity regulation", "Motion smooth",
    "Joint configuration tracking", "Target / object proximity",
    "Temporal requirement", "Outcome-based success",
]

PI_INPUTS = ["πinput_Joint and segment kinematics", "πinput_Muscle-related states",
             "πinput_Time or phase", "πinput_Historical information", "πinput_Contact"]

PI_OUTPUTS = ["πoutput_Muscle activation", "πoutput_Muscle excitation",
              "πoutput_Kinematic", "πoutput_Synergy", "πoutput_Muscle length"]

PARADIGMS = ["Behavior cloning", "Biologically inspired", "Exploration",
             "Curriculum learning", "Multi-task learning"]

CONTRIBUTIONS = ["Methodological Contribution", "Application Contribution",
                 "Knowledge-Generating Contribution"]

EVALUATIONS = ["Evaluation_Kinematics", "Evaluation_Torque", "Evaluation_Performance",
               "Evaluation_Muscle act.or Metabolic", "Evaluation_GRF", "Qual. visual"]
