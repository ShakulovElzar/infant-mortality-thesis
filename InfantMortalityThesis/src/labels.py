"""Value labels for the variables used in Table 1 (codes from reference/columns.csv)."""

YN = {"Y": "Yes", "N": "No", "U": "Unknown"}

TABLE1_VARS = {
    "MAGER9": ("Mother's age", {"1": "<15", "2": "15-19", "3": "20-24", "4": "25-29", "5": "30-34",
                                "6": "35-39", "7": "40-44", "8": "45-49", "9": "50-54"}),
    "MRACEHISP": ("Mother's race/Hispanic origin", {"1": "NH White", "2": "NH Black", "3": "NH AIAN",
                                                     "4": "NH Asian", "5": "NH NHOPI", "6": "NH more than one race",
                                                     "7": "Hispanic", "8": "Unknown"}),
    "MBSTATE_REC": ("Mother's nativity", {"1": "Born in the U.S.", "2": "Born outside the U.S.", "3": "Unknown"}),
    "MEDUC": ("Mother's education", {"1": "8th grade or less", "2": "9-12th, no diploma", "3": "High school/GED",
                                      "4": "Some college", "5": "Associate", "6": "Bachelor's", "7": "Master's",
                                      "8": "Doctorate/professional", "9": "Unknown"}),
    "PAY_REC": ("Payment source", {"1": "Medicaid", "2": "Private insurance", "3": "Self-pay", "4": "Other", "9": "Unknown"}),
    "LBO_REC": ("Live birth order", {"1": "1st", "2": "2nd", "3": "3rd", "4": "4th", "5": "5th", "6": "6th",
                                     "7": "7th", "8": "8th or more", "9": "Unknown"}),
    "CIG0_R": ("Cigarettes per day before pregnancy", {"0": "None", "1": "1-5", "2": "6-10", "3": "11-20",
                                                        "4": "21-40", "5": "41+", "6": "Unknown"}),
    "BMI_R": ("Pre-pregnancy BMI", {"1": "Underweight <18.5", "2": "Normal 18.5-24.9", "3": "Overweight 25.0-29.9",
                                    "4": "Obesity I 30.0-34.9", "5": "Obesity II 35.0-39.9",
                                    "6": "Obesity III >=40", "9": "Unknown"}),
    "RF_PDIAB": ("Pre-pregnancy diabetes", YN),
    "RF_GDIAB": ("Gestational diabetes", YN),
    "RF_PHYPE": ("Pre-pregnancy hypertension", YN),
    "RF_GHYPE": ("Gestational hypertension", YN),
    "DPLURAL": ("Plurality", {"1": "Single", "2": "Twin", "3": "Triplet", "4": "Quadruplet+", "5": "Code 5 (not in guide; 2016-2019 only)"}),
    "SEX": ("Infant sex", {"M": "Male", "F": "Female"}),
}
