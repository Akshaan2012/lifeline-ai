from __future__ import annotations

from typing import Any

from backend.openai_helper import openai_json


BASE_ADVICE = {
    "Self-Care": {
        "doctor_visit": "You may monitor symptoms at home for now.",
        "timeframe": "Watch for changes over the next 24 to 48 hours.",
        "care": [
            "Rest and drink enough water.",
            "Track temperature, pain level, and any new symptoms.",
            "Use simple home care first, and avoid guessing strong medicines.",
        ],
    },
    "Doctor Visit Recommended": {
        "doctor_visit": "A doctor visit is recommended.",
        "timeframe": "Book a visit within 1 to 2 days, sooner if symptoms worsen.",
        "care": [
            "Write down symptoms, when they started, and medicines already taken.",
            "Carry allergy details and existing medical conditions.",
            "Keep monitoring temperature, pulse, oxygen, sugar, or BP if available.",
        ],
    },
    "Urgent Care": {
        "doctor_visit": "You should visit urgent care or a hospital quickly.",
        "timeframe": "Try to get medical care today.",
        "care": [
            "Do not ignore symptoms or wait many days.",
            "Ask someone to stay with you or take you to care.",
            "Carry medication details, allergies, and previous reports.",
        ],
    },
    "Emergency": {
        "doctor_visit": "Seek emergency help now.",
        "timeframe": "Do not wait. Arrange help immediately.",
        "care": [
            "Call local emergency services or go to the nearest emergency department.",
            "Do not drive yourself if you feel faint, confused, breathless, or very weak.",
            "Keep the patient sitting or lying safely while help is arranged.",
        ],
    },
}

CATEGORY_GUIDANCE = {
    "Respiratory": {
        "likely_pattern": "This may fit a breathing or respiratory problem, such as cough, airway irritation, asthma-like symptoms, or infection.",
        "home_care": ["Rest in a well-ventilated room.", "Drink warm fluids if comfortable.", "Use prescribed inhalers only as directed."],
        "avoid": ["Avoid smoke, dust, strong smells, and heavy exercise.", "Do not use someone else's inhaler or antibiotics.", "Do not ignore low oxygen or worsening breathlessness."],
        "precautions": ["Wear a mask if coughing.", "Keep distance from others if infection is possible.", "Monitor breathing and oxygen if you have a pulse oximeter."],
        "prevention": ["Wash hands often.", "Keep rooms ventilated.", "Avoid smoking.", "Stay updated with vaccines recommended by a doctor."],
        "red_flags": ["Trouble breathing.", "Oxygen below 94%.", "Chest pain.", "Blue lips.", "Unable to speak full sentences."],
        "doctor_questions": ["Could this be asthma, pneumonia, allergy, or infection?", "Do I need oxygen check, chest exam, or medicine?", "When should I come back if it worsens?"],
    },
    "Heart Warning": {
        "likely_pattern": "This may fit a heart warning pattern, especially if chest pain, sweating, fainting, or breathlessness is present.",
        "home_care": ["Stop physical activity.", "Sit or lie down safely.", "Ask someone to stay nearby."],
        "avoid": ["Do not ignore chest pressure.", "Do not drive yourself if symptoms are serious.", "Do not take extra heart medicine unless prescribed for this situation."],
        "precautions": ["Treat chest pain with sweating or breathlessness as serious.", "Keep medication and allergy details ready.", "Call emergency help if symptoms are strong or sudden."],
        "prevention": ["Check blood pressure regularly.", "Avoid smoking.", "Exercise safely.", "Manage diabetes, cholesterol, sleep, and stress."],
        "red_flags": ["Chest pain with sweating.", "Pain spreading to arm, jaw, back, or shoulder.", "Severe breathlessness.", "Fainting.", "New weakness or confusion."],
        "doctor_questions": ["Do I need an ECG or heart check?", "Is this chest pain heart-related?", "What signs mean I should go to emergency immediately?"],
    },
    "Infection/Fever": {
        "likely_pattern": "This may fit a fever or infection pattern. The cause could be viral, bacterial, or another illness, so watch duration and severity.",
        "home_care": ["Rest.", "Drink fluids.", "Keep the room comfortable.", "Use fever medicine only as directed on the label or by a doctor."],
        "avoid": ["Do not overuse antibiotics.", "Do not take multiple medicines with the same ingredient.", "Avoid spreading infection to others."],
        "precautions": ["Track temperature in Celsius.", "Avoid close contact if contagious symptoms are present.", "Seek care faster for babies, elderly people, pregnancy, or weak immunity."],
        "prevention": ["Wash hands.", "Avoid close contact with sick people.", "Eat balanced food.", "Sleep well.", "Keep recommended vaccines updated."],
        "red_flags": ["Fever above 39.4 C.", "Fever lasting more than 3 days.", "Confusion.", "Stiff neck.", "Seizure.", "Rash with fever.", "Breathing trouble."],
        "doctor_questions": ["Could this be viral or bacterial?", "Do I need a test?", "What medicine is safe for fever?", "When should I return if fever continues?"],
    },
    "Digestive": {
        "likely_pattern": "This may fit a stomach or digestion problem, such as food-related illness, infection, acidity, or dehydration risk.",
        "home_care": ["Take small sips of water or ORS.", "Eat light food when hungry.", "Rest your stomach if vomiting."],
        "avoid": ["Avoid oily, spicy, or spoiled food.", "Avoid alcohol.", "Do not take strong painkillers without advice if stomach pain is severe."],
        "precautions": ["Watch for dehydration.", "Keep track of vomiting or diarrhea frequency.", "Use safe water and clean food."],
        "prevention": ["Wash hands before meals.", "Drink safe water.", "Store food safely.", "Avoid doubtful street food when hygiene is poor."],
        "red_flags": ["Blood in stool.", "Severe stomach pain.", "Continuous vomiting.", "Very little urination.", "Dizziness or extreme weakness.", "Fever with severe abdominal pain."],
        "doctor_questions": ["Could this be food poisoning, infection, acidity, or appendicitis?", "Do I need fluids or tests?", "What should I eat and avoid?"],
    },
    "Diabetes Warning": {
        "likely_pattern": "This may fit a blood sugar warning pattern, especially with thirst, frequent urination, fatigue, or blurred vision.",
        "home_care": ["Avoid sugary drinks.", "Drink water.", "Check blood sugar if you have a glucometer.", "Eat balanced meals instead of skipping food."],
        "avoid": ["Do not ignore repeated high sugar symptoms.", "Do not stop diabetes medicine without advice.", "Avoid very sugary foods and drinks."],
        "precautions": ["Book a blood sugar check.", "Watch for dehydration.", "Carry current medicine details to the doctor."],
        "prevention": ["Exercise regularly if safe.", "Maintain healthy weight.", "Eat more fiber.", "Reduce refined sugar.", "Sleep regularly."],
        "red_flags": ["Very high sugar with vomiting.", "Confusion.", "Fast breathing.", "Severe weakness.", "Fainting.", "Fruity-smelling breath."],
        "doctor_questions": ["Do I need fasting sugar, HbA1c, or urine test?", "What diet changes should I follow?", "Do I need medicine or a dose review?"],
    },
    "Neurological": {
        "likely_pattern": "This may fit a nerve or brain warning pattern, especially with severe headache, confusion, seizure, dizziness, or stroke-like signs.",
        "home_care": ["Rest in a safe place.", "Ask someone to stay nearby.", "Avoid driving if dizzy, confused, or weak."],
        "avoid": ["Do not ignore sudden weakness or speech trouble.", "Do not take random strong pain medicines for sudden severe headache.", "Avoid screens and bright light if headache is migraine-like."],
        "precautions": ["Note when symptoms started.", "Check for face drooping, arm weakness, and speech trouble.", "Seek urgent help for sudden neurological symptoms."],
        "prevention": ["Sleep regularly.", "Stay hydrated.", "Manage blood pressure and diabetes.", "Avoid head injury.", "Track headache triggers."],
        "red_flags": ["Face drooping.", "Arm weakness.", "Speech trouble.", "Seizure.", "Sudden worst headache.", "Confusion.", "Fainting.", "New vision loss."],
        "doctor_questions": ["Could this be migraine, stroke warning, seizure, or blood pressure-related?", "Do I need urgent imaging or tests?", "What signs mean emergency care?"],
    },
    "Skin/Allergy": {
        "likely_pattern": "This may fit an allergy or skin reaction pattern, especially with rash, itching, swelling, or trigger exposure.",
        "home_care": ["Avoid the suspected trigger.", "Keep the area clean.", "Use cool compresses for itching if comfortable."],
        "avoid": ["Do not scratch hard.", "Do not apply unknown creams on open skin.", "Do not rely on tablets alone if breathing or swelling symptoms occur."],
        "precautions": ["Note new foods, medicines, insect bites, or products.", "Check if rash is spreading.", "Watch for lip, tongue, or throat swelling."],
        "prevention": ["Know your allergies.", "Read medicine and food labels.", "Avoid known triggers.", "Carry prescribed allergy medicine if advised."],
        "red_flags": ["Swelling of lips, tongue, or throat.", "Breathing difficulty.", "Rash with dizziness or fainting.", "Severe allergic reaction.", "Skin infection with fever."],
        "doctor_questions": ["Could this be allergy, infection, or medicine reaction?", "Do I need allergy medicine or testing?", "What triggers should I avoid?"],
    },
    "General Health": {
        "likely_pattern": "The symptoms do not strongly match one category, so the safest approach is to monitor changes and use the doctor-visit recommendation.",
        "home_care": ["Rest.", "Drink water.", "Track symptoms.", "Avoid heavy activity if you feel weak."],
        "avoid": ["Avoid self-medicating with strong medicines.", "Do not ignore symptoms that get worse quickly.", "Do not mix medicines without checking safety."],
        "precautions": ["Write down symptom start time, severity, and triggers.", "Ask for help if symptoms affect daily life.", "Use the Q&A page for general education."],
        "prevention": ["Sleep well.", "Exercise regularly.", "Eat balanced meals.", "Manage stress.", "Keep routine health checks updated."],
        "red_flags": ["Symptoms get worse quickly.", "Severe pain.", "Chest pain.", "Breathing trouble.", "Fainting.", "Confusion.", "Weakness on one side."],
        "doctor_questions": ["What could be causing these symptoms?", "Do I need tests?", "What should I do if symptoms continue?"],
    },
}


def _risk_summary(risk_level: str) -> str:
    summaries = {
        "Self-Care": "Low immediate risk based on entered details, but symptoms should still be watched.",
        "Doctor Visit Recommended": "Moderate risk. A medical review is safer, especially if symptoms continue.",
        "Urgent Care": "High risk. The symptoms or vitals suggest care should not be delayed.",
        "Emergency": "Critical risk. The entered details include danger signs that need immediate help.",
    }
    return summaries[risk_level]


def build_recommendations(triage_result: Any) -> dict[str, Any]:
    base = BASE_ADVICE[triage_result.risk_level]
    category = CATEGORY_GUIDANCE.get(triage_result.possible_category, CATEGORY_GUIDANCE["General Health"])

    advice = {
        "doctor_visit": base["doctor_visit"],
        "timeframe": base["timeframe"],
        "care_steps": base["care"],
        "likely_pattern": category["likely_pattern"],
        "home_care": category["home_care"],
        "avoid": category["avoid"],
        "precautions": category["precautions"],
        "prevention": category["prevention"],
        "red_flags": category["red_flags"],
        "doctor_questions": category["doctor_questions"],
        "risk_summary": _risk_summary(triage_result.risk_level),
        "simple_explanation": triage_result.explanation,
        "disclaimer": "This is general guidance only. It does not replace a doctor, diagnosis, prescription, or emergency service.",
    }
    return _ai_enhanced_recommendations(triage_result, advice)


def _ai_enhanced_recommendations(triage_result: Any, advice: dict[str, Any]) -> dict[str, Any]:
    system = (
        "You are LifeLine AI's patient health checker assistant. Return only valid JSON. "
        "Improve patient-friendly wording while preserving the risk level and safety intent. "
        "Do not diagnose, prescribe, or replace emergency care."
    )
    user = (
        "Enhance these recommendation fields as JSON with exact keys: likely_pattern string, "
        "care_steps array, home_care array, avoid array, precautions array, prevention array, "
        "red_flags array, doctor_questions array, simple_explanation string. "
        "Keep arrays to 3-5 short strings. "
        f"Risk level: {triage_result.risk_level}\nScore: {triage_result.score}\n"
        f"Possible category: {triage_result.possible_category}\nSignals: {', '.join(triage_result.signals)}\n"
        f"Existing advice: {advice}"
    )
    data = openai_json(system, user, max_output_tokens=620)
    if not data:
        return advice

    enhanced = dict(advice)

    def items(name: str) -> list[str]:
        value = data.get(name)
        if not isinstance(value, list):
            return list(advice.get(name, []))
        clean = [str(item).strip() for item in value if str(item).strip()]
        return clean[:5] or list(advice.get(name, []))

    for key in ["care_steps", "home_care", "avoid", "precautions", "prevention", "red_flags", "doctor_questions"]:
        enhanced[key] = items(key)
    for key in ["likely_pattern", "simple_explanation"]:
        if str(data.get(key) or "").strip():
            enhanced[key] = str(data[key]).strip()
    enhanced["source"] = "OpenAI-enhanced guidance with LifeLine AI safety rules."
    return enhanced
