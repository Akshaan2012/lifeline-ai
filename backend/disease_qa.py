from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

import requests

from backend.openai_helper import openai_json


DISEASE_LIBRARY: dict[str, dict[str, Any]] = {
    "alzheimers": {
        "title": "Alzheimer's",
        "meaning": "Alzheimer's is a brain condition that slowly affects memory, thinking, and daily activities.",
        "symptoms": ["Forgetting recent events.", "Getting confused in familiar places.", "Trouble finding words.", "Mood or behavior changes."],
        "precautions": ["Use reminders and notes.", "Keep the home safe and simple.", "Do not ignore sudden confusion."],
        "prevention": ["Stay mentally active.", "Exercise regularly.", "Control blood pressure, sugar, and sleep problems."],
        "doctor": "Visit a doctor if memory problems affect daily life.",
        "emergency": ["Sudden confusion.", "Fainting.", "Weakness on one side of the body."],
    },
    "parkinsons": {
        "title": "Parkinson's",
        "meaning": "Parkinson's is a brain condition that can make movement slower and cause shaking, stiffness, or balance problems.",
        "symptoms": ["Shaking hands or fingers.", "Slow movement.", "Muscle stiffness.", "Balance problems.", "Smaller handwriting."],
        "precautions": ["Prevent falls.", "Use support while walking if needed.", "Do not stop medicines without a doctor."],
        "prevention": ["There is no sure prevention, but exercise and healthy habits may support brain health.", "Manage sleep and stress.", "Avoid head injuries."],
        "doctor": "See a neurologist if shaking, stiffness, or slow movement continues.",
        "emergency": ["Sudden weakness.", "Severe confusion.", "Major fall or injury."],
    },
    "diabetes": {
        "title": "Diabetes",
        "meaning": "Diabetes means blood sugar stays higher than normal because the body cannot use sugar properly.",
        "symptoms": ["Frequent urination.", "Excessive thirst.", "Tiredness.", "Blurred vision.", "Slow wound healing."],
        "precautions": ["Avoid sugary drinks.", "Check sugar if possible.", "Take prescribed medicine on time."],
        "prevention": ["Exercise often.", "Eat more whole foods and fiber.", "Maintain a healthy weight."],
        "doctor": "Visit a doctor if high sugar symptoms continue or you have repeated abnormal sugar readings.",
        "emergency": ["Confusion.", "Vomiting with high sugar.", "Fast breathing or severe weakness."],
    },
    "asthma": {
        "title": "Asthma",
        "meaning": "Asthma is a breathing condition where airways become narrow, swollen, or sensitive.",
        "symptoms": ["Wheezing.", "Coughing.", "Chest tightness.", "Shortness of breath."],
        "precautions": ["Avoid smoke and dust.", "Use prescribed inhalers correctly.", "Keep rescue medicine nearby if prescribed."],
        "prevention": ["Know your triggers.", "Keep rooms clean.", "Follow an asthma action plan from a doctor."],
        "doctor": "See a doctor if breathing symptoms happen often or disturb sleep.",
        "emergency": ["Severe breathing difficulty.", "Blue lips.", "Rescue inhaler not helping."],
    },
    "fever": {
        "title": "Fever",
        "meaning": "Fever means body temperature is higher than normal, often because the body is fighting an infection.",
        "symptoms": ["High temperature.", "Chills.", "Body pain.", "Weakness.", "Sweating."],
        "precautions": ["Rest.", "Drink fluids.", "Avoid taking antibiotics without a doctor."],
        "prevention": ["Wash hands.", "Avoid close contact with sick people.", "Keep vaccines updated where appropriate."],
        "doctor": "Visit a doctor if fever lasts more than 3 days or keeps coming back.",
        "emergency": ["Fever above 39.4 C.", "Confusion.", "Stiff neck, seizure, or breathing trouble."],
    },
    "hypertension": {
        "title": "High Blood Pressure",
        "meaning": "High blood pressure means blood pushes too strongly against blood vessel walls.",
        "symptoms": ["Often no symptoms.", "Headache.", "Dizziness.", "Chest discomfort in serious cases."],
        "precautions": ["Check blood pressure regularly.", "Reduce salt.", "Take prescribed medicine on time."],
        "prevention": ["Exercise.", "Maintain healthy weight.", "Limit salty and processed food.", "Manage stress."],
        "doctor": "See a doctor for repeated readings above normal.",
        "emergency": ["Blood pressure around 180/120 or higher.", "Chest pain.", "Severe headache, confusion, or weakness."],
    },
    "migraine": {
        "title": "Migraine",
        "meaning": "Migraine is a type of headache that can cause strong pain, nausea, and sensitivity to light or sound.",
        "symptoms": ["Throbbing headache.", "Nausea.", "Light or sound sensitivity.", "Vision changes before headache."],
        "precautions": ["Rest in a quiet dark room.", "Drink water.", "Avoid known triggers."],
        "prevention": ["Sleep on time.", "Eat regular meals.", "Track headache triggers.", "Manage stress."],
        "doctor": "Visit a doctor if headaches are frequent, new, or affecting daily life.",
        "emergency": ["Sudden worst headache.", "Weakness.", "Confusion.", "Fever with stiff neck."],
    },
    "tuberculosis": {
        "title": "Tuberculosis",
        "meaning": "Tuberculosis, or TB, is an infection that usually affects the lungs and can spread through the air.",
        "symptoms": ["Cough for weeks.", "Fever.", "Night sweats.", "Weight loss.", "Chest pain."],
        "precautions": ["Cover coughs.", "Avoid close contact until checked.", "Take TB medicine exactly as prescribed."],
        "prevention": ["Get tested after exposure.", "Improve ventilation.", "Complete treatment to stop spread."],
        "doctor": "Visit a doctor if cough lasts more than 2 weeks or you have night sweats and weight loss.",
        "emergency": ["Coughing blood.", "Severe breathing trouble.", "Chest pain."],
    },
    "pneumonia": {
        "title": "Pneumonia",
        "meaning": "Pneumonia is a lung infection that can make breathing hard and cause cough, fever, and weakness.",
        "symptoms": ["Cough.", "Fever.", "Chest pain.", "Shortness of breath.", "Tiredness."],
        "precautions": ["Rest.", "Drink fluids.", "Avoid smoke.", "Monitor oxygen if available."],
        "prevention": ["Wash hands.", "Avoid smoking.", "Ask a doctor about vaccines if at risk."],
        "doctor": "Visit a doctor if cough, fever, or breathing symptoms are getting worse.",
        "emergency": ["Oxygen below 94%.", "Severe breathing difficulty.", "Blue lips or confusion."],
    },
    "arthritis": {
        "title": "Arthritis",
        "meaning": "Arthritis means joint inflammation. It can cause pain, swelling, and stiffness.",
        "symptoms": ["Joint pain.", "Swelling.", "Stiffness.", "Reduced movement."],
        "precautions": ["Avoid overloading painful joints.", "Use gentle movement.", "Do not ignore swollen or hot joints."],
        "prevention": ["Maintain healthy weight.", "Exercise gently.", "Protect joints from injury."],
        "doctor": "See a doctor if joint pain lasts, worsens, or affects movement.",
        "emergency": ["Joint pain with fever.", "Severe swelling.", "Sudden inability to move a joint."],
    },
    "anemia": {
        "title": "Anemia",
        "meaning": "Anemia means the body does not have enough healthy red blood cells to carry oxygen well.",
        "symptoms": ["Tiredness.", "Weakness.", "Pale skin.", "Dizziness.", "Shortness of breath."],
        "precautions": ["Do not ignore severe weakness.", "Avoid taking iron tablets without knowing the cause.", "Eat iron-rich foods if advised."],
        "prevention": ["Eat balanced food.", "Treat heavy bleeding.", "Check blood levels if symptoms continue."],
        "doctor": "Visit a doctor for repeated tiredness, dizziness, or pale skin.",
        "emergency": ["Chest pain.", "Fainting.", "Severe shortness of breath."],
    },
    "covid": {
        "title": "COVID-19",
        "meaning": "COVID-19 is a viral infection that can affect breathing and the whole body.",
        "symptoms": ["Fever.", "Cough.", "Sore throat.", "Tiredness.", "Loss of taste or smell.", "Breathing trouble."],
        "precautions": ["Rest.", "Avoid spreading infection.", "Wear a mask around others.", "Monitor oxygen if possible."],
        "prevention": ["Wash hands.", "Improve ventilation.", "Stay updated with vaccines recommended by health authorities."],
        "doctor": "Visit a doctor if symptoms worsen or you are high risk.",
        "emergency": ["Oxygen below 94%.", "Severe breathing trouble.", "Chest pain or confusion."],
    },
    "malaria": {
        "title": "Malaria",
        "meaning": "Malaria is an infection spread by mosquito bites. It can cause fever, chills, sweating, and weakness.",
        "symptoms": ["Fever.", "Chills.", "Sweating.", "Headache.", "Body pain.", "Weakness."],
        "precautions": ["Avoid mosquito bites.", "Use mosquito nets or repellents.", "Do not ignore repeated fever after travel or mosquito exposure."],
        "prevention": ["Remove standing water.", "Use window screens or nets.", "Take preventive medicine if a doctor recommends it for travel."],
        "doctor": "Visit a doctor for fever with chills, especially in areas where malaria is common.",
        "emergency": ["Confusion.", "Seizure.", "Severe weakness.", "Yellow eyes, dark urine, or breathing trouble."],
    },
    "dengue": {
        "title": "Dengue",
        "meaning": "Dengue is a viral infection spread by mosquitoes. It can cause high fever and body pain.",
        "symptoms": ["High fever.", "Severe body pain.", "Headache.", "Pain behind eyes.", "Rash.", "Nausea."],
        "precautions": ["Drink fluids.", "Avoid aspirin or ibuprofen unless a doctor says it is safe.", "Watch for bleeding or severe stomach pain."],
        "prevention": ["Prevent mosquito bites.", "Remove standing water.", "Use repellents and window screens."],
        "doctor": "Visit a doctor if dengue is suspected or fever is high.",
        "emergency": ["Bleeding.", "Severe stomach pain.", "Continuous vomiting.", "Drowsiness or cold hands and feet."],
    },
    "typhoid": {
        "title": "Typhoid",
        "meaning": "Typhoid is a bacterial infection usually spread through unsafe food or water.",
        "symptoms": ["Long fever.", "Headache.", "Weakness.", "Stomach pain.", "Diarrhea or constipation."],
        "precautions": ["Drink safe water.", "Avoid street food if hygiene is doubtful.", "Take antibiotics only as prescribed."],
        "prevention": ["Wash hands.", "Eat safely prepared food.", "Consider vaccination if advised."],
        "doctor": "Visit a doctor for fever lasting several days with stomach symptoms.",
        "emergency": ["Severe stomach pain.", "Confusion.", "Blood in stool.", "Very weak or dehydrated."],
    },
    "stroke": {
        "title": "Stroke",
        "meaning": "A stroke happens when blood flow to part of the brain is blocked or bleeding happens in the brain.",
        "symptoms": ["Face drooping.", "Arm weakness.", "Speech trouble.", "Sudden confusion.", "Sudden vision or balance problems."],
        "precautions": ["Do not wait to see if symptoms pass.", "Note the time symptoms started.", "Keep the person safe and still."],
        "prevention": ["Control blood pressure.", "Manage diabetes and cholesterol.", "Avoid smoking.", "Exercise regularly."],
        "doctor": "Stroke symptoms need emergency care immediately.",
        "emergency": ["Any face drooping, arm weakness, or speech trouble.", "Sudden severe headache.", "Sudden confusion or weakness."],
    },
    "heart attack": {
        "title": "Heart Attack",
        "meaning": "A heart attack happens when blood flow to the heart is blocked.",
        "symptoms": ["Chest pressure or pain.", "Sweating.", "Shortness of breath.", "Pain in arm, jaw, back, or shoulder.", "Nausea."],
        "precautions": ["Stop activity.", "Call emergency help.", "Do not drive yourself if symptoms are serious."],
        "prevention": ["Avoid smoking.", "Control blood pressure, sugar, and cholesterol.", "Exercise and eat heart-healthy foods."],
        "doctor": "Possible heart attack symptoms need emergency care now.",
        "emergency": ["Chest pain with sweating.", "Severe breathlessness.", "Fainting.", "Pain spreading to arm or jaw."],
    },
    "epilepsy": {
        "title": "Epilepsy",
        "meaning": "Epilepsy is a condition where a person has repeated seizures because of unusual electrical activity in the brain.",
        "symptoms": ["Seizures.", "Staring spells.", "Body jerking.", "Confusion after an episode.", "Loss of awareness."],
        "precautions": ["Do not put anything in the mouth during a seizure.", "Move sharp objects away.", "Turn the person on their side if possible."],
        "prevention": ["Take prescribed medicine regularly.", "Sleep well.", "Avoid known seizure triggers."],
        "doctor": "Visit a doctor or neurologist for any seizure or repeated episodes.",
        "emergency": ["Seizure lasting more than 5 minutes.", "Repeated seizures.", "Injury, pregnancy, or breathing trouble."],
    },
    "depression": {
        "title": "Depression",
        "meaning": "Depression is a mental health condition that can cause long-lasting sadness, low energy, and loss of interest.",
        "symptoms": ["Sad mood.", "Loss of interest.", "Sleep changes.", "Low energy.", "Hopeless feelings.", "Difficulty concentrating."],
        "precautions": ["Talk to someone trusted.", "Avoid alcohol or drugs.", "Do not stay alone if you feel unsafe."],
        "prevention": ["Keep a routine.", "Sleep regularly.", "Exercise gently.", "Stay connected with supportive people."],
        "doctor": "Visit a mental health professional if symptoms last more than 2 weeks or affect daily life.",
        "emergency": ["Thoughts of self-harm.", "Feeling unsafe.", "Planning to hurt yourself or someone else."],
    },
    "anxiety": {
        "title": "Anxiety",
        "meaning": "Anxiety is strong worry or fear that can affect the body and daily life.",
        "symptoms": ["Fast heartbeat.", "Worry.", "Restlessness.", "Sweating.", "Trouble sleeping.", "Panic attacks."],
        "precautions": ["Try slow breathing.", "Reduce caffeine.", "Talk to a trusted person."],
        "prevention": ["Sleep well.", "Exercise.", "Limit stimulants.", "Practice stress management."],
        "doctor": "Visit a doctor or counselor if anxiety is frequent or affects daily life.",
        "emergency": ["Chest pain.", "Fainting.", "Thoughts of self-harm.", "Feeling out of control."],
    },
    "kidney stones": {
        "title": "Kidney Stones",
        "meaning": "Kidney stones are hard mineral pieces that can form in the kidney and cause severe pain.",
        "symptoms": ["Severe side or back pain.", "Pain while urinating.", "Blood in urine.", "Nausea.", "Frequent urination."],
        "precautions": ["Drink water if you can.", "Do not ignore fever with urinary pain.", "Use pain medicine only as directed."],
        "prevention": ["Drink enough water.", "Reduce excess salt.", "Follow diet advice based on stone type."],
        "doctor": "Visit a doctor for severe side pain, blood in urine, or repeated urinary pain.",
        "emergency": ["Fever with kidney pain.", "Unable to urinate.", "Severe pain or vomiting."],
    },
    "hepatitis": {
        "title": "Hepatitis",
        "meaning": "Hepatitis means inflammation of the liver. It can happen due to viruses, alcohol, medicines, or other causes.",
        "symptoms": ["Yellow eyes or skin.", "Dark urine.", "Tiredness.", "Nausea.", "Stomach pain.", "Loss of appetite."],
        "precautions": ["Avoid alcohol.", "Do not share needles or razors.", "Ask a doctor before taking medicines."],
        "prevention": ["Practice safe hygiene.", "Use vaccines for hepatitis A and B if advised.", "Avoid unsafe injections."],
        "doctor": "Visit a doctor if eyes or skin look yellow, urine is dark, or liver symptoms appear.",
        "emergency": ["Confusion.", "Severe stomach swelling.", "Vomiting blood.", "Extreme weakness."],
    },
}

MEDICINE_LIBRARY: dict[str, dict[str, Any]] = {
    "paracetamol": {
        "title": "Paracetamol / Acetaminophen",
        "meaning": "Paracetamol, also called acetaminophen, is commonly used for fever and mild to moderate pain.",
        "symptoms": ["Used for fever.", "Used for headache, body pain, tooth pain, or mild pain.", "It does not treat the cause of infection."],
        "precautions": ["Do not take more than the label or doctor says.", "Avoid mixing multiple medicines that also contain paracetamol.", "Ask a doctor first if you have liver disease or heavy alcohol use."],
        "prevention": ["Store medicine safely away from children.", "Read labels carefully.", "Use the lowest safe amount for the shortest needed time."],
        "doctor": "Ask a doctor if fever lasts more than 3 days, pain is severe, or you are unsure about safe use.",
        "emergency": ["Accidental overdose.", "Severe allergy.", "Yellow eyes, severe vomiting, confusion, or extreme sleepiness after taking it."],
        "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a681004.html",
    },
    "ibuprofen": {
        "title": "Ibuprofen",
        "meaning": "Ibuprofen is a pain and fever medicine. It also reduces swelling and inflammation.",
        "symptoms": ["Used for pain, fever, swelling, cramps, or inflammation.", "It may upset the stomach in some people.", "It is not suitable for everyone."],
        "precautions": ["Avoid it if a doctor told you not to take NSAIDs.", "Ask a doctor first if you have stomach ulcers, kidney disease, blood thinners, or are pregnant.", "Take it only as the label or doctor says."],
        "prevention": ["Take medicines with proper guidance.", "Avoid combining similar pain medicines unless advised.", "Keep a list of your medicines."],
        "doctor": "Ask a doctor if pain or fever continues, or if you have kidney, stomach, heart, or bleeding problems.",
        "emergency": ["Black stools.", "Vomiting blood.", "Severe allergic reaction.", "Chest pain or severe breathing trouble."],
        "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a682159.html",
    },
    "aspirin": {
        "title": "Aspirin",
        "meaning": "Aspirin can reduce pain and fever, and in some people it is used as a blood thinner under medical advice.",
        "symptoms": ["Used for pain or fever in some cases.", "May be prescribed for heart or stroke prevention.", "Can increase bleeding risk."],
        "precautions": ["Do not give aspirin to children unless a doctor says so.", "Ask a doctor first if you take blood thinners or have ulcers.", "Do not start aspirin for heart protection without medical advice."],
        "prevention": ["Follow the exact plan given by a doctor.", "Tell doctors before surgery or dental work if you take aspirin.", "Avoid mixing with other blood-thinning medicines unless advised."],
        "doctor": "Ask a doctor before using aspirin regularly or if you have bleeding, ulcers, asthma, or kidney problems.",
        "emergency": ["Severe bleeding.", "Black stools.", "Vomiting blood.", "Signs of stroke or heart attack."],
        "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a682878.html",
    },
    "amoxicillin": {
        "title": "Amoxicillin",
        "meaning": "Amoxicillin is an antibiotic used for some bacterial infections. It does not work for viral infections like common cold.",
        "symptoms": ["Used only when a bacterial infection is likely or confirmed.", "Needs the correct dose and duration from a doctor.", "Wrong use can cause resistance."],
        "precautions": ["Do not take antibiotics without a prescription.", "Tell the doctor if you are allergic to penicillin.", "Complete the course exactly if prescribed."],
        "prevention": ["Avoid sharing antibiotics.", "Do not save leftover antibiotics for later.", "Use antibiotics only when needed."],
        "doctor": "See a doctor if you think you need antibiotics or symptoms are worsening.",
        "emergency": ["Breathing trouble.", "Swelling of lips or face.", "Severe rash.", "Severe diarrhea or dehydration."],
        "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a685001.html",
    },
    "antibiotics": {
        "title": "Antibiotics",
        "meaning": "Antibiotics treat some bacterial infections. They do not treat most viral fevers, colds, flu, or dengue-like illnesses.",
        "symptoms": ["They should be used only when a doctor suspects bacteria.", "Using them when not needed can cause resistance.", "They can cause allergy, diarrhea, stomach upset, or side effects."],
        "precautions": ["Do not start antibiotics just because you have fever.", "Do not share leftover antibiotics.", "Tell a doctor about allergies, pregnancy, kidney/liver disease, and other medicines."],
        "prevention": ["Use antibiotics only with a prescription.", "Complete the prescribed course exactly when a doctor gives one.", "Prevent infections with handwashing, vaccines, safe food/water, and mosquito control."],
        "doctor": "Ask a doctor if fever is high, lasts more than 3 days, keeps returning, or comes with red flags like breathing trouble, confusion, rash, severe pain, dehydration, or stiff neck.",
        "emergency": ["Breathing trouble.", "Confusion.", "Blue lips.", "Severe allergic reaction.", "Very high fever with stiff neck.", "Signs of dehydration."],
        "source": "CDC: https://www.cdc.gov/antibiotic-use/about/index.html",
    },
    "cetirizine": {
        "title": "Cetirizine",
        "meaning": "Cetirizine is an antihistamine used for allergy symptoms like sneezing, itching, runny nose, or hives.",
        "symptoms": ["Used for allergies.", "Can reduce itching or hives.", "May cause sleepiness in some people."],
        "precautions": ["Be careful with driving if it makes you sleepy.", "Ask a doctor first for young children, pregnancy, kidney disease, or other medicines.", "Do not use it to treat severe allergic reactions alone."],
        "prevention": ["Avoid known allergy triggers.", "Keep rooms clean and low-dust if dust allergy is present.", "Follow allergy plans from a doctor."],
        "doctor": "Ask a doctor if allergy symptoms are frequent, severe, or not improving.",
        "emergency": ["Breathing difficulty.", "Swelling of lips, tongue, or throat.", "Dizziness or fainting with rash."],
        "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a698026.html",
    },
    "metformin": {
        "title": "Metformin",
        "meaning": "Metformin is a prescription medicine commonly used to help control blood sugar in type 2 diabetes.",
        "symptoms": ["Used for diabetes management.", "Works best with food, activity, and doctor follow-up.", "Can cause stomach upset in some people."],
        "precautions": ["Do not start or stop it without a doctor.", "Tell your doctor about kidney disease, liver disease, heavy alcohol use, or scans with contrast dye.", "Take it as prescribed."],
        "prevention": ["Monitor blood sugar as advised.", "Eat balanced meals.", "Exercise regularly if safe for you."],
        "doctor": "Contact a doctor for repeated high or low sugar, side effects, or before changing diabetes medicine.",
        "emergency": ["Confusion.", "Severe weakness.", "Fast breathing.", "Very low sugar symptoms or severe vomiting."],
        "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a696005.html",
    },
    "insulin": {
        "title": "Insulin",
        "meaning": "Insulin is a prescription medicine that helps control blood sugar. It is used by some people with diabetes.",
        "symptoms": ["Used to lower high blood sugar.", "Must be taken exactly as prescribed.", "Can cause low blood sugar if food, dose, or activity do not match."],
        "precautions": ["Do not change dose without medical advice.", "Know signs of low sugar.", "Store insulin as instructed."],
        "prevention": ["Check blood sugar as advised.", "Carry quick sugar if you are at risk of low sugar.", "Keep meals and medicine timing consistent."],
        "doctor": "Ask a doctor for dose changes, frequent low sugar, or repeated high sugar.",
        "emergency": ["Fainting.", "Seizure.", "Confusion.", "Very low sugar or very high sugar with vomiting."],
        "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a682611.html",
    },
    "salbutamol": {
        "title": "Salbutamol / Albuterol Inhaler",
        "meaning": "Salbutamol, also called albuterol, is a rescue inhaler used to quickly open airways during asthma or wheezing.",
        "symptoms": ["Used for wheezing or asthma attacks.", "Works quickly for many people.", "Needing it often may mean asthma is not controlled."],
        "precautions": ["Use the inhaler technique taught by a doctor.", "Do not ignore worsening breathing.", "Keep it available if prescribed."],
        "prevention": ["Avoid asthma triggers.", "Use controller medicines if prescribed.", "Follow an asthma action plan."],
        "doctor": "See a doctor if you need the rescue inhaler often or symptoms disturb sleep.",
        "emergency": ["Severe breathing difficulty.", "Blue lips.", "Inhaler not helping.", "Unable to speak full sentences."],
        "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a682145.html",
    },
    "ors": {
        "title": "ORS",
        "meaning": "ORS means oral rehydration solution. It helps replace water and salts lost during diarrhea, vomiting, or dehydration.",
        "symptoms": ["Used for dehydration from diarrhea or vomiting.", "Helps replace fluids and salts.", "It does not stop the cause of diarrhea."],
        "precautions": ["Mix ORS exactly as the packet says.", "Use clean water.", "Do not add extra sugar or salt."],
        "prevention": ["Drink safe water.", "Wash hands.", "Eat clean food."],
        "doctor": "See a doctor if diarrhea or vomiting is severe, long-lasting, or in a baby/elderly person.",
        "emergency": ["Very little urination.", "Extreme weakness.", "Blood in stool.", "Sunken eyes, confusion, or severe dehydration."],
        "source": "WHO: https://www.who.int/news-room/fact-sheets/detail/diarrhoeal-disease",
    },
}

ALIASES = {
    "alzheimer": "alzheimers",
    "alzheimers disease": "alzheimers",
    "parkinson": "parkinsons",
    "parkinsons disease": "parkinsons",
    "sugar": "diabetes",
    "high sugar": "diabetes",
    "bp": "hypertension",
    "blood pressure": "hypertension",
    "high bp": "hypertension",
    "tb": "tuberculosis",
    "coronavirus": "covid",
    "covid-19": "covid",
    "joint pain": "arthritis",
    "low hemoglobin": "anemia",
    "heartattack": "heart attack",
    "seizure": "epilepsy",
    "fits": "epilepsy",
    "kidney stone": "kidney stones",
    "yellow fever": "hepatitis",
    "jaundice": "hepatitis",
    "acetaminophen": "paracetamol",
    "crocin": "paracetamol",
    "tylenol": "paracetamol",
    "advil": "ibuprofen",
    "brufen": "ibuprofen",
    "antibiotic": "antibiotics",
    "antibiotics": "antibiotics",
    "allergy tablet": "cetirizine",
    "zyrtec": "cetirizine",
    "diabetes medicine": "metformin",
    "inhaler": "salbutamol",
    "albuterol": "salbutamol",
    "oral rehydration solution": "ors",
}

STOP_WORDS = {
    "what", "is", "are", "the", "a", "an", "about", "tell", "me", "of", "for",
    "symptoms", "signs", "prevention", "prevent", "precautions", "cure", "treatment",
    "disease", "condition", "early", "how", "can", "i", "to", "in", "and", "or",
    "should", "need", "needed", "during", "after", "go", "hospital", "serious",
    "feel", "does", "do", "it", "my", "why", "when", "eat", "contagious",
}

CATEGORY_GUIDANCE = {
    "infection": {
        "precautions": ["Rest and drink fluids.", "Avoid spreading infection to others.", "Do not take antibiotics unless a doctor prescribes them."],
        "prevention": ["Wash hands often.", "Avoid close contact with sick people.", "Keep recommended vaccines updated."],
        "emergency": ["Breathing trouble.", "Confusion.", "Very high fever or symptoms getting worse fast."],
    },
    "heart": {
        "precautions": ["Avoid heavy activity if chest pain or breathlessness is present.", "Monitor blood pressure if available.", "Do not ignore chest discomfort."],
        "prevention": ["Exercise safely.", "Avoid smoking.", "Control blood pressure, sugar, cholesterol, and stress."],
        "emergency": ["Chest pain with sweating.", "Pain spreading to arm, jaw, or back.", "Fainting or severe breathlessness."],
    },
    "brain": {
        "precautions": ["Avoid driving if confused, dizzy, or weak.", "Ask someone to stay nearby.", "Track symptoms clearly."],
        "prevention": ["Sleep well.", "Control blood pressure and sugar.", "Stay mentally and physically active."],
        "emergency": ["Face drooping.", "Arm weakness.", "Speech trouble, seizure, or sudden worst headache."],
    },
    "respiratory": {
        "precautions": ["Avoid smoke and dust.", "Rest and monitor breathing.", "Use prescribed inhalers or medicines correctly."],
        "prevention": ["Avoid smoking.", "Keep air clean and ventilated.", "Wash hands and avoid infection exposure."],
        "emergency": ["Oxygen below 94%.", "Blue lips.", "Severe breathing difficulty."],
    },
    "digestive": {
        "precautions": ["Eat light food.", "Take small sips of fluid.", "Avoid oily or spoiled food."],
        "prevention": ["Wash hands before meals.", "Drink safe water.", "Store food safely."],
        "emergency": ["Blood in stool.", "Severe stomach pain.", "Continuous vomiting or dehydration."],
    },
    "skin": {
        "precautions": ["Avoid scratching.", "Avoid suspected triggers.", "Keep the area clean and dry."],
        "prevention": ["Know allergies.", "Use gentle skin products.", "Avoid sharing towels during infections."],
        "emergency": ["Swelling of lips or tongue.", "Breathing difficulty.", "Rash with fainting or dizziness."],
    },
    "general": {
        "precautions": ["Monitor symptoms.", "Avoid self-medicating with strong medicines.", "Write down symptoms and when they started."],
        "prevention": ["Sleep well.", "Drink water.", "Eat balanced food and exercise regularly."],
        "emergency": ["Chest pain.", "Breathing trouble.", "Fainting, confusion, severe weakness, or symptoms getting worse fast."],
    },
}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def _title_from_question(question: str) -> str:
    text = _normalize(question)
    for phrase in ["what is", "tell me about", "explain", "symptoms of", "signs of", "prevention of", "precautions for"]:
        text = text.replace(phrase, " ")
    words = [word for word in text.split() if word not in STOP_WORDS]
    if not words:
        return "general health"
    return " ".join(words[:4]).title()


def _find_local_key(question: str) -> str | None:
    normalized = _normalize(question)
    for alias, disease_key in ALIASES.items():
        if _normalize(alias) in normalized:
            return disease_key
    for disease_key, answer in DISEASE_LIBRARY.items():
        title = _normalize(str(answer["title"]))
        if disease_key in normalized or title in normalized:
            return disease_key
    return None


def _find_medicine_key(question: str) -> str | None:
    normalized = _normalize(question)
    for alias, medicine_key in ALIASES.items():
        if medicine_key in MEDICINE_LIBRARY and _normalize(alias) in normalized:
            return medicine_key
    for medicine_key, answer in MEDICINE_LIBRARY.items():
        title = _normalize(str(answer["title"]))
        if medicine_key in normalized or title in normalized:
            return medicine_key
    return None


def _looks_like_medicine_question(question: str) -> bool:
    normalized = _normalize(question)
    keywords = [
        "medicine", "tablet", "capsule", "syrup", "injection", "dose", "dosage",
        "side effect", "drug", "antibiotic", "painkiller", "can i take", "should i take",
    ]
    return any(keyword in normalized for keyword in keywords)


def _medicine_relationship_answer(question: str) -> dict[str, Any] | None:
    normalized = _normalize(question)
    if "paracetamol" in normalized or "acetaminophen" in normalized or "crocin" in normalized:
        if "antibiotic" in normalized:
            return {
                "title": "Paracetamol and antibiotics",
                "meaning": "No. Paracetamol is not an antibiotic. It can reduce fever or pain, but it does not kill bacteria.",
                "symptoms": [
                    "Paracetamol helps with fever and mild pain.",
                    "Antibiotics are used for some bacterial infections only.",
                    "A fever does not automatically mean you need antibiotics.",
                ],
                "precautions": [
                    "Do not take more paracetamol than the label or doctor says.",
                    "Do not start antibiotics unless a doctor prescribes them.",
                    "Check other cold/flu medicines because they may also contain paracetamol.",
                ],
                "prevention": [
                    "For fever, rest and drink fluids unless a doctor told you to limit fluids.",
                    "Watch symptoms and temperature.",
                    "Use the Health Checker if you are unsure how serious the symptoms are.",
                ],
                "doctor": "Ask a doctor if fever lasts more than 3 days, is very high, keeps coming back, or comes with breathing trouble, confusion, stiff neck, rash, dehydration, or severe pain.",
                "emergency": ["Breathing trouble.", "Confusion.", "Severe allergy.", "Accidental overdose.", "Very high fever with stiff neck or seizure."],
                "kind": "medicine",
                "intent": "comparison",
                "source": "MedlinePlus: https://medlineplus.gov/druginfo/meds/a681004.html | CDC: https://www.cdc.gov/antibiotic-use/about/index.html",
                "safety_note": "This is general medicine information. It cannot tell you the exact dose or confirm if this medicine is safe for you personally.",
            }
    return None


def _question_intent(question: str) -> str:
    normalized = _normalize(question)
    intent_words = {
        "production": ["made", "make", "manufacture", "manufactured", "produce", "produced", "production"],
        "emergency": ["emergency", "hospital", "urgent", "danger", "serious", "red flag", "when to go"],
        "tests": ["test", "scan", "diagnose", "diagnosis", "blood test", "x ray", "mri", "ct"],
        "treatment": ["treat", "treatment", "cure", "manage", "relief", "what should i do"],
        "prevention": ["prevent", "prevention", "avoid", "reduce risk", "protect"],
        "contagious": ["contagious", "spread", "catch", "infectious", "transmit"],
        "food": ["eat", "food", "diet", "drink", "avoid eating"],
        "cause": ["cause", "why", "reason"],
        "side_effects": ["side effect", "reaction", "safe", "safety"],
    }
    for intent, words in intent_words.items():
        if any(word in normalized for word in words):
            return intent
    return "overview"


def _topic_from_question(question: str) -> str:
    local_key = _find_local_key(question)
    if local_key:
        return str(DISEASE_LIBRARY[local_key]["title"])
    medicine_key = _find_medicine_key(question)
    if medicine_key:
        return str(MEDICINE_LIBRARY[medicine_key]["title"])
    return _title_from_question(question)


def _general_health_answer(question: str) -> dict[str, Any]:
    topic = _topic_from_question(question)
    category = _detect_category(question + " " + topic)
    guidance = CATEGORY_GUIDANCE[category]
    intent = _question_intent(question)

    meaning_by_intent = {
        "emergency": f"For {topic}, the most important thing is to know when it may be unsafe to wait.",
        "tests": f"Testing for {topic} depends on the symptoms, exam, age, and risk factors.",
        "treatment": f"Care for {topic} depends on the cause and how severe the symptoms are.",
        "prevention": f"Prevention for {topic} means lowering risk and acting early when symptoms appear.",
        "contagious": f"Whether {topic} spreads to others depends on the exact cause.",
        "food": f"Food and drink advice for {topic} depends on the exact condition and symptoms.",
        "cause": f"{topic} can have more than one possible cause, so symptoms and timing matter.",
        "side_effects": f"Side effects and safety depend on the medicine, dose, person, and other health conditions.",
        "overview": f"Here is a simple health answer about {topic}.",
    }
    symptoms_by_intent = {
        "emergency": guidance["emergency"],
        "tests": ["A doctor may ask about symptoms and medical history.", "They may check vital signs and examine the affected area.", "Tests may include blood, urine, imaging, or swabs depending on the problem."],
        "treatment": ["Rest, fluids, and monitoring may help mild problems.", "Medicines should match the cause, not just the symptom.", "Avoid using strong medicines without professional advice."],
        "prevention": guidance["prevention"],
        "contagious": ["Fever, cough, diarrhea, rash, or infected wounds can sometimes spread.", "Handwashing, masks when coughing, and avoiding close contact can reduce spread.", "A doctor or test may be needed to know for sure."],
        "food": ["Drink enough safe fluids unless a doctor has restricted fluids.", "Choose simple, balanced food if appetite is low.", "Avoid alcohol, spoiled food, and anything that clearly worsens symptoms."],
        "cause": ["Infections, inflammation, injury, allergies, lifestyle factors, or long-term conditions can cause symptoms.", "The same symptom can have mild or serious causes.", "Duration and severity help decide what to do next."],
        "side_effects": ["Check the active ingredient and warning label.", "Allergy, breathing trouble, swelling, fainting, or overdose symptoms need urgent help.", "Ask a pharmacist before mixing medicines."],
        "overview": ["Symptoms can vary from person to person.", "Use the Patient Health Checker if you have symptoms now.", "A doctor can confirm the cause with an exam or tests."],
    }
    doctor_by_intent = {
        "emergency": "Get urgent medical help now if any red flag is present.",
        "tests": "See a doctor if symptoms continue, worsen, or you need a clear diagnosis.",
        "treatment": "See a doctor if symptoms are severe, not improving, or you are unsure what is safe.",
        "prevention": "Ask a doctor for prevention advice if you are high-risk, pregnant, elderly, a child, or have long-term illness.",
        "contagious": "Ask a doctor if symptoms may spread to others, especially fever, rash, diarrhea, or ongoing cough.",
        "food": "Ask a doctor quickly if you cannot keep fluids down, have severe weakness, or have blood in vomit/stool.",
        "cause": "See a doctor if the cause is unclear, symptoms continue, or symptoms affect daily life.",
        "side_effects": "Ask a doctor or pharmacist before starting, stopping, mixing, or changing medicines.",
        "overview": f"Visit a doctor if you are worried about {topic}, symptoms continue, or daily life is affected.",
    }

    return {
        "title": topic,
        "meaning": meaning_by_intent[intent],
        "symptoms": symptoms_by_intent[intent],
        "precautions": guidance["precautions"],
        "prevention": guidance["prevention"],
        "doctor": doctor_by_intent[intent],
        "emergency": guidance["emergency"],
        "kind": "general",
        "intent": intent,
        "source": "LifeLine AI general health safety guide. For exact diagnosis or treatment, use a clinician or verified medical source.",
    }


def _adapt_known_disease_answer(answer: dict[str, Any], question: str) -> dict[str, Any]:
    intent = _question_intent(question)
    if intent == "overview":
        answer["intent"] = intent
        return answer

    title = str(answer["title"])
    category = _detect_category(question + " " + title)
    guidance = CATEGORY_GUIDANCE[category]
    answer["intent"] = intent
    if intent == "tests":
        answer["meaning"] = f"Tests for {title} depend on your symptoms, exam, age, and risk factors."
        answer["symptoms"] = [
            "A doctor may start with questions and a physical exam.",
            "Common tests may include blood tests, urine tests, imaging, swabs, or specialist tests depending on the problem.",
            "The right test depends on what the doctor is trying to confirm or rule out.",
        ]
        answer["doctor"] = f"See a doctor if you think you may have {title} or need testing."
    elif intent == "treatment":
        answer["meaning"] = f"Treatment for {title} depends on the cause and severity."
        answer["symptoms"] = [
            "Mild symptoms may need monitoring and supportive care.",
            "Medicines or procedures should match the confirmed cause.",
            "Do not start prescription medicines without a clinician.",
        ]
    elif intent == "prevention":
        answer["meaning"] = f"Prevention for {title} focuses on lowering risk and acting early."
        answer["symptoms"] = answer["prevention"]
    elif intent == "emergency":
        answer["meaning"] = f"For {title}, these warning signs mean it may be unsafe to wait."
        answer["symptoms"] = answer["emergency"]
        answer["doctor"] = "Get urgent medical help now if any red flag is present."
    elif intent == "contagious":
        answer["meaning"] = f"Whether {title} spreads to others depends on the exact cause."
        answer["symptoms"] = [
            "Some infections spread through air, touch, food/water, blood, sex, or insects.",
            "Handwashing, masks when coughing, and avoiding close contact can reduce spread.",
            "A doctor or test may be needed to know if it is contagious.",
        ]
    elif intent == "food":
        answer["meaning"] = f"Food and drink advice for {title} depends on symptoms and the exact condition."
        answer["symptoms"] = [
            "Drink safe fluids unless a doctor has restricted fluids.",
            "Choose simple balanced food if appetite is low.",
            "Avoid alcohol, spoiled food, and anything that clearly worsens symptoms.",
        ]
    elif intent == "cause":
        answer["meaning"] = f"{title} can have different causes or risk factors."
        answer["symptoms"] = [
            "Symptoms, timing, age, medical history, and exposures help find the cause.",
            "The same symptom can have mild or serious causes.",
            "A doctor may need tests to confirm the reason.",
        ]
    elif intent == "side_effects":
        answer["meaning"] = f"If you are asking about medicine safety related to {title}, be careful with self-treatment."
        answer["symptoms"] = [
            "Check medicine labels and active ingredients.",
            "Ask a pharmacist before mixing medicines.",
            "Allergy, breathing trouble, swelling, fainting, or overdose symptoms need urgent help.",
        ]
    answer["precautions"] = answer.get("precautions", guidance["precautions"])
    answer["prevention"] = answer.get("prevention", guidance["prevention"])
    answer["emergency"] = answer.get("emergency", guidance["emergency"])
    return answer


def _finalize_answer(answer: dict[str, Any], question: str) -> dict[str, Any]:
    topic = str(answer.get("title", _title_from_question(question)))
    kind = answer.get("kind", "general")
    category = _detect_category(question + " " + topic)
    base_steps = {
        "infection": ["Rest and drink safe fluids.", "Avoid spreading infection to others.", "Track fever, breathing, pain, and hydration."],
        "heart": ["Stop heavy activity if chest pain or breathlessness is present.", "Check blood pressure if available.", "Do not ignore symptoms that feel new or severe."],
        "brain": ["Do not drive if dizzy, confused, weak, or sleepy.", "Ask someone to stay nearby if symptoms are strong.", "Write down when symptoms started."],
        "respiratory": ["Avoid smoke, dust, and heavy activity.", "Sit upright if breathing feels difficult.", "Use prescribed inhalers exactly as instructed."],
        "digestive": ["Take small sips of fluid often.", "Eat light food if you can.", "Watch for dehydration, blood, or severe pain."],
        "skin": ["Avoid scratching.", "Keep the area clean and dry.", "Avoid the suspected trigger if you know it."],
        "general": ["Monitor symptoms and timing.", "Avoid guessing with strong medicines.", "Use the Health Checker if you have symptoms now."],
    }
    if kind == "medicine":
        answer["what_to_do_now"] = [
            "Check the active ingredient on the label.",
            "Use it only for the reason it is meant for.",
            "Ask a pharmacist or doctor before mixing it with other medicines.",
        ]
        answer["avoid"] = [
            "Do not guess doses.",
            "Do not share prescription medicines.",
            "Do not use old or expired medicine.",
        ]
        answer["doctor_questions"] = [
            "Is this medicine safe for my age and health conditions?",
            "Can it interact with my other medicines?",
            "What side effects should make me stop and get help?",
        ]
    else:
        answer["what_to_do_now"] = base_steps.get(category, base_steps["general"])
        answer["avoid"] = [
            "Do not ignore symptoms that are getting worse.",
            "Do not delay urgent care if a red flag appears.",
            "Do not use antibiotics or strong medicines unless prescribed.",
        ]
        answer["doctor_questions"] = [
            f"What is the most likely cause of {topic}?",
            "Do I need any tests or follow-up?",
            "What signs mean I should seek urgent help?",
        ]
    return answer


def _medicine_answer(question: str) -> dict[str, Any] | None:
    key = _find_medicine_key(question)
    if not key:
        return None
    answer = dict(MEDICINE_LIBRARY[key])
    answer["kind"] = "medicine"
    answer["intent"] = _question_intent(question)
    answer["source"] = answer.get("source", "LifeLine AI medicine safety guide")
    answer["safety_note"] = (
        "This is general medicine information. It cannot tell you the exact dose or confirm if this medicine is safe for you personally."
    )
    if key == "antibiotics" and answer["intent"] == "production":
        answer["title"] = "How antibiotics are made"
        answer["meaning"] = (
            "Antibiotics are made in licensed pharmaceutical labs and factories, not at home. "
            "Many start from bacteria or fungi grown in large sterile tanks; others are made or improved with chemical synthesis."
        )
        answer["symptoms"] = [
            "Microbes that naturally produce an antibiotic may be grown in controlled fermentation tanks.",
            "The antibiotic is separated, purified, and tested for strength, safety, and contamination.",
            "The active ingredient is then made into tablets, capsules, liquids, creams, or injections under strict quality control.",
        ]
        answer["precautions"] = [
            "Do not try to make or extract antibiotics at home.",
            "Only use antibiotics that come from a licensed pharmacy or healthcare service.",
            "Poor-quality or wrongly used antibiotics can fail treatment, cause harm, and increase antibiotic resistance.",
        ]
        answer["prevention"] = [
            "Use antibiotics only when prescribed.",
            "Complete the course exactly as the doctor says if one is prescribed.",
            "Prevent infections with handwashing, vaccines, safe food/water, and proper wound care.",
        ]
        answer["doctor"] = "Ask a doctor or pharmacist if you want to know which antibiotic is used for a specific infection or why it was prescribed."
    if any(word in _normalize(question) for word in ["dose", "dosage", "how much", "how many"]):
        answer["doctor"] = (
            "For dose, follow the medicine label or your doctor's prescription. "
            "Dose depends on age, weight, diagnosis, other medicines, pregnancy, allergies, and kidney/liver health."
        )
    return answer


def _safe_unknown_medicine_answer(question: str) -> dict[str, Any]:
    topic = _title_from_question(question)
    return {
        "title": topic,
        "meaning": f"I do not have a trusted detailed offline medicine card for {topic} yet. I can still give safe medicine guidance.",
        "symptoms": [
            "Use medicines only for the right reason.",
            "Check the label for active ingredient, warnings, and expiry date.",
            "Tell a doctor or pharmacist about allergies, pregnancy, other medicines, and existing conditions.",
        ],
        "precautions": [
            "Do not start, stop, or mix prescription medicines without medical advice.",
            "Do not share antibiotics or leftover medicines.",
            "Avoid guessing doses, especially for children.",
        ],
        "prevention": [
            "Keep a list of medicines you take.",
            "Store medicines away from children.",
            "Ask a pharmacist if two medicines can be taken together.",
        ],
        "doctor": "Ask a doctor or pharmacist for the correct medicine and dose for your situation.",
        "emergency": ["Severe allergy.", "Breathing trouble.", "Fainting.", "Accidental overdose.", "Severe sleepiness or confusion after medicine."],
        "kind": "medicine",
        "source": "Safe medicine fallback. No personalized dosage given.",
        "safety_note": (
            "This is general medicine information. It cannot tell you the exact dose or confirm if this medicine is safe for you personally."
        ),
    }


def _detect_category(text: str) -> str:
    value = _normalize(text)
    if any(word in value for word in ["virus", "bacteria", "infection", "fever", "flu", "malaria", "dengue", "typhoid", "tuberculosis"]):
        return "infection"
    if any(word in value for word in ["heart", "cardiac", "blood pressure", "cholesterol", "stroke", "chest pain"]):
        return "heart"
    if any(word in value for word in ["brain", "nerve", "memory", "parkinson", "alzheimer", "seizure", "migraine", "dizzy", "dizziness"]):
        return "brain"
    if any(word in value for word in ["lung", "breath", "asthma", "pneumonia", "cough", "respiratory"]):
        return "respiratory"
    if any(word in value for word in ["stomach", "liver", "kidney", "bowel", "digest", "diarrhea", "vomit"]):
        return "digestive"
    if any(word in value for word in ["skin", "rash", "allergy", "eczema", "itch"]):
        return "skin"
    return "general"


def _wiki_summary(topic: str) -> dict[str, str] | None:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
    headers = {"User-Agent": "LifeLineAIStudentProject/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code != 200:
            return None
        data = response.json()
    except Exception:
        return None

    extract = str(data.get("extract", "")).strip()
    title = str(data.get("title", topic)).strip()
    if len(extract) < 40 or data.get("type") == "disambiguation":
        return None
    return {"title": title, "extract": extract, "url": str(data.get("content_urls", {}).get("desktop", {}).get("page", ""))}


def _internet_answer(question: str) -> dict[str, Any] | None:
    topic = _title_from_question(question)
    summary = _wiki_summary(topic)
    if not summary:
        return None

    category = _detect_category(summary["extract"] + " " + topic)
    guidance = CATEGORY_GUIDANCE[category]
    meaning = summary["extract"].split(". ")[0]
    if not meaning.endswith("."):
        meaning += "."

    return {
        "title": summary["title"],
        "meaning": meaning,
        "symptoms": [
            "Symptoms can be different for each person.",
            "Use the Patient Health Checker if you want guidance based on your exact symptoms.",
            "A doctor can confirm the condition with proper examination or tests.",
        ],
        "precautions": guidance["precautions"],
        "prevention": guidance["prevention"],
        "doctor": f"Visit a doctor if you think you may have {summary['title']}, symptoms continue, or symptoms affect daily life.",
        "emergency": guidance["emergency"],
        "source": f"Public summary: {summary['url'] or 'Wikipedia'}",
    }


def _safe_unknown_answer(question: str) -> dict[str, Any]:
    topic = _title_from_question(question)
    guidance = CATEGORY_GUIDANCE[_detect_category(topic)]
    return {
        "title": topic,
        "meaning": f"I do not have a trusted detailed offline answer for {topic} yet. I can still give safe general guidance and help you decide when to see a doctor.",
        "symptoms": [
            "Symptoms depend on the exact condition and the person.",
            "Use the Patient Health Checker if you already have symptoms.",
            "For diagnosis, a doctor may need an exam, history, and tests.",
        ],
        "precautions": guidance["precautions"],
        "prevention": guidance["prevention"],
        "doctor": f"Visit a doctor if you are worried about {topic}, symptoms continue, or daily life is affected.",
        "emergency": guidance["emergency"],
        "source": "Safe fallback answer. Internet lookup was unavailable or no reliable summary was found.",
    }


def _ai_health_answer(question: str) -> dict[str, Any] | None:
    system = (
        "You are LifeLine AI's health education assistant. Return only valid JSON. "
        "Give simple, cautious, patient-friendly general health education. Do not diagnose, prescribe, "
        "calculate doses, or say a medicine is personally safe. Include emergency warning signs when relevant."
    )
    user = (
        "Answer this health or medicine question as JSON with these exact keys: "
        "title string, meaning string, symptoms array of 2-4 strings, precautions array of 2-4 strings, "
        "prevention array of 2-4 strings, doctor string, emergency array of 2-4 strings, kind string, "
        "intent string, source string, safety_note string. "
        f"Question: {question}"
    )
    data = openai_json(system, user, max_output_tokens=520)
    if not data:
        return None

    required = ["title", "meaning", "symptoms", "precautions", "prevention", "doctor", "emergency"]
    if any(key not in data for key in required):
        return None
    answer = {
        "title": str(data.get("title") or _title_from_question(question)),
        "meaning": str(data.get("meaning") or ""),
        "symptoms": [str(item) for item in data.get("symptoms", []) if str(item).strip()][:4],
        "precautions": [str(item) for item in data.get("precautions", []) if str(item).strip()][:4],
        "prevention": [str(item) for item in data.get("prevention", []) if str(item).strip()][:4],
        "doctor": str(data.get("doctor") or "Ask a doctor if symptoms continue, worsen, or you are unsure what is safe."),
        "emergency": [str(item) for item in data.get("emergency", []) if str(item).strip()][:4],
        "kind": str(data.get("kind") or "general"),
        "intent": str(data.get("intent") or _question_intent(question)),
        "source": str(data.get("source") or "OpenAI general health education with LifeLine AI safety rules."),
    }
    safety_note = str(data.get("safety_note") or "").strip()
    if safety_note:
        answer["safety_note"] = safety_note
    if not answer["symptoms"] or not answer["precautions"] or not answer["emergency"]:
        return None
    return answer


def answer_question(question: str) -> dict[str, Any]:
    relationship_answer = _medicine_relationship_answer(question)
    if relationship_answer:
        return _finalize_answer(relationship_answer, question)

    medicine_answer = _medicine_answer(question)
    if medicine_answer:
        return _finalize_answer(medicine_answer, question)

    key = _find_local_key(question)
    if key:
        answer = dict(DISEASE_LIBRARY[key])
        answer["kind"] = "disease"
        answer["source"] = "LifeLine AI local knowledge base"
        return _finalize_answer(_adapt_known_disease_answer(answer, question), question)

    if _looks_like_medicine_question(question):
        ai_answer = _ai_health_answer(question)
        if ai_answer:
            ai_answer["kind"] = "medicine"
            ai_answer["safety_note"] = ai_answer.get(
                "safety_note",
                "This is general medicine information. It cannot tell you the exact dose or confirm if this medicine is safe for you personally.",
            )
            return _finalize_answer(ai_answer, question)
        return _finalize_answer(_safe_unknown_medicine_answer(question), question)

    internet_answer = _internet_answer(question)
    if internet_answer:
        internet_answer["kind"] = "disease"
        return _finalize_answer(internet_answer, question)

    ai_answer = _ai_health_answer(question)
    if ai_answer:
        return _finalize_answer(ai_answer, question)

    return _finalize_answer(_general_health_answer(question), question)
