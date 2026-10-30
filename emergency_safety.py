
"""
Dengue AI Guardian - Emergency Safety Engine

This module checks reported symptoms for dengue warning signs.
It is an educational safety tool, not a diagnostic system.
"""

import re


# WHO-recognized dengue warning signs
WARNING_SIGNS = {
    "severe abdominal pain": [
        "severe abdominal pain",
        "severe stomach pain",
        "intense stomach pain",
        "severe tummy pain",
        "ಹೊಟ್ಟೆಯಲ್ಲಿ ತೀವ್ರ ನೋವು",
        "ಹೊಟ್ಟೆ ನೋವು ಜಾಸ್ತಿ"
    ],
    "persistent vomiting": [
        "persistent vomiting",
        "continuous vomiting",
        "repeated vomiting",
        "vomiting continuously",
        "ನಿರಂತರ ವಾಂತಿ",
        "ಮತ್ತೆ ಮತ್ತೆ ವಾಂತಿ"
    ],
    "bleeding": [
        "bleeding",
        "bleeding gums",
        "nose bleeding",
        "blood in vomit",
        "blood in stool",
        "ರಕ್ತಸ್ರಾವ",
        "ಮೂಗಿನಿಂದ ರಕ್ತ",
        "ಒಸಡಿನಿಂದ ರಕ್ತ"
    ],
    "rapid breathing": [
        "rapid breathing",
        "difficulty breathing",
        "breathing difficulty",
        "fast breathing",
        "ಉಸಿರಾಟದ ತೊಂದರೆ",
        "ಉಸಿರಾಡಲು ಕಷ್ಟ"
    ],
    "extreme fatigue or restlessness": [
        "extreme fatigue",
        "restlessness",
        "extreme weakness",
        "unusually tired",
        "ತೀವ್ರ ಸುಸ್ತು",
        "ತೀವ್ರ ದೌರ್ಬಲ್ಯ"
    ],
    "pale or cold skin": [
        "pale skin",
        "cold skin",
        "cold clammy skin",
        "ಚರ್ಮ ತಣ್ಣಗಾಗುವುದು",
        "ಚರ್ಮ ಬಿಳಿಚಿಕೊಳ್ಳುವುದು"
    ]
}


def check_emergency_symptoms(user_input):
    """
    Check user-reported symptoms for warning signs.

    Returns an emergency alert when warning signs are detected.
    This function does not diagnose dengue.
    """

    text = user_input.lower().strip()

    detected_signs = []

    for sign, keywords in WARNING_SIGNS.items():

        for keyword in keywords:

            pattern = r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)"

            if re.search(pattern, text):
                detected_signs.append(sign)
                break

    if detected_signs:

        return {
            "status": "URGENT_MEDICAL_EVALUATION",
            "alert": True,
            "detected_warning_signs": detected_signs,
            "message": (
                "WARNING: Possible dengue warning signs reported. "
                "Seek urgent medical evaluation at a hospital now. "
                "Do not wait for an AI response or attempt self-diagnosis."
            ),
            "kannada_message": (
                "ಎಚ್ಚರಿಕೆ: ಅಪಾಯದ ಲಕ್ಷಣಗಳು ವರದಿಯಾಗಿವೆ. "
                "ತಕ್ಷಣ ಆಸ್ಪತ್ರೆಗೆ ತೆರಳಿ ವೈದ್ಯಕೀಯ ಪರೀಕ್ಷೆ ಮಾಡಿಸಿಕೊಳ್ಳಿ. "
                "AI ಉತ್ತರಕ್ಕಾಗಿ ಕಾಯಬೇಡಿ."
            )
        }

    return {
        "status": "NO_WARNING_SIGN_MATCHED",
        "alert": False,
        "detected_warning_signs": [],
        "message": (
            "No listed warning signs were matched in the text. "
            "This does not rule out dengue or guarantee safety. "
            "Consult a healthcare professional if symptoms are present "
            "or worsening."
        ),
        "kannada_message": (
            "ಪಟ್ಟಿಯಲ್ಲಿರುವ ಅಪಾಯದ ಲಕ್ಷಣಗಳು ಪತ್ತೆಯಾಗಿಲ್ಲ. "
            "ಆದರೆ ಇದರಿಂದ ಡೆಂಗ್ಯೂ ಇಲ್ಲ ಅಥವಾ ಅಪಾಯವಿಲ್ಲ ಎಂದು "
            "ಖಚಿತಪಡಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ. ಲಕ್ಷಣಗಳು ಇದ್ದರೆ ಅಥವಾ "
            "ಹದಗೆಟ್ಟರೆ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ."
        )
    }


if __name__ == "__main__":

    print("\nDENGUE AI GUARDIAN")
    print("Emergency Safety Engine Test")
    print("-" * 40)

    symptoms = input(
        "\nDescribe your symptoms (English or Kannada): "
    )

    result = check_emergency_symptoms(symptoms)

    print("\nSTATUS:", result["status"])
    print("ALERT:", result["alert"])

    if result["detected_warning_signs"]:
        print("Detected warning signs:")
        for sign in result["detected_warning_signs"]:
            print("-", sign)

    print("\nEnglish:")
    print(result["message"])

    print("\nKannada:")
    print(result["kannada_message"])
