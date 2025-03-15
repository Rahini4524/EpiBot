import numpy as np
from flask import Flask, request, jsonify, send_from_directory
import torch
from torchvision import models, transforms
from PIL import Image
from sklearn.tree import DecisionTreeClassifier
import joblib
import google.cloud.dialogflow_v2 as dialogflow
import json
from flask_cors import CORS




app = Flask(__name__, static_folder="EpiBot", static_url_path="")
CORS(app)

model = models.resnet18(pretrained=False)  


num_classes = 10
model.fc = torch.nn.Linear(model.fc.in_features, num_classes)


# Define the image transformations (Make sure it matches your training transformations)
model.load_state_dict(torch.load(r"skin_disease_model.pth", map_location=torch.device("cpu")))
model.eval()

# Load trained Decision Tree model for symptom-based classification
dt_model = joblib.load(r"decision_tree_model.pkl")

class_names = [
    "Eczema", "Melanoma", "Atopic Dermatitis", "Basal Cell Carcinoma", 
    "Melanocytic Nevi","Benign Keratosis-like Lesions", "Psoriasis/Lichen Planus", "Seborrheic Keratosis",
    "Fungal Infection", "Warts/Molluscum"
]

disease_symptom_map = {
    "Eczema": ["itching", "redness", "dry skin", "scaling"],    
    "Atopic Dermatitis": ["itching", "redness", "Swelling", "dry skin"],
    "Psoriasis": ["scaling", "redness", "white patches"],
    "Fungal Infection": ["itching", "redness", "blisters", "white patches", "scaling"],
    "Melanoma": ["itching","dark spots / pigmentation", "lumps or growths"],
    "Basal Cell Carcinoma": ["lumps or growths", "open wounds / pus"],
    "Benign Tumors": ["lumps or growths"],
    "Warts / Molluscum": ["lumps or growths", "scaling"],
    "Seborrheic Keratosis": ["dark spots / pigmentation", "scaling"],
}
symptoms_order = [
    "itching", "redness", "burning", "pain", "swelling", "scaling", "blisters", "open wounds / pus",
    "white patches", "lumps or growths", "dark spots / pigmentation", "dry skin"
]

recommendations = {
    "Eczema": "🩹 Recommendations:\n"
              "- Keep skin moisturized using fragrance-free creams.\n"
              "- Avoid hot showers and harsh soaps.\n"
              "- Wear soft, breathable fabrics (like cotton).\n"
              "- Use anti-itch creams like hydrocortisone if needed.\n"
              "- Consult a dermatologist for severe cases.",

    "Atopic Dermatitis": "🩹 Recommendations:\n"
                         "- Apply a thick moisturizer daily.\n"
                         "- Avoid known triggers like allergens, perfumes, and stress.\n"
                         "- Use anti-inflammatory creams as prescribed.\n"
                         "- Consider antihistamines for itching.\n"
                         "- Consult a doctor if symptoms persist.",

    "Psoriasis": "🩹 Recommendations:\n"
                 "- Keep skin hydrated with thick moisturizers.\n"
                 "- Avoid smoking, alcohol, and stress.\n"
                 "- Try mild sunlight exposure, but avoid sunburn.\n"
                 "- Use medicated shampoos if scalp is affected.\n"
                 "- Seek a dermatologist for advanced treatments.",

    "Fungal Infection": "🩹 Recommendations:\n"
                        "- Keep affected areas clean and dry.\n"
                        "- Use antifungal creams or powders.\n"
                        "- Avoid sharing personal items like towels.\n"
                        "- Wear breathable footwear if affecting feet.\n"
                        "- See a doctor if symptoms worsen.",

    "Melanoma": "⚠️ **URGENT:** **Consult a dermatologist immediately!**\n"
                "- Avoid sun exposure and use high SPF sunscreen.\n"
                "- Do not ignore moles that change in shape, color, or size.\n"
                "- Early detection is crucial; consider a biopsy if advised.\n"
                "- Wear protective clothing when outdoors.",

    "Basal Cell Carcinoma": "🩹 Recommendations:\n"
                            "- **Consult a dermatologist as soon as possible.**\n"
                            "- Avoid excessive sun exposure.\n"
                            "- Use broad-spectrum sunscreen daily.\n"
                            "- Surgical removal may be necessary.",

    "Benign Keratosis-like Lesions": "🩹 Recommendations:\n"
                     "- **Most benign tumors are harmless**, but monitor for changes.\n"
                     "- Avoid excessive sun exposure.\n"
                     "- If growth increases or changes in texture, consult a doctor.\n"
                     "- Surgical removal is an option for cosmetic or medical reasons.",

    "Warts / Molluscum": "🩹 Recommendations:\n"
                         "- Avoid scratching or picking at the lesions.\n"
                         "- Use over-the-counter salicylic acid treatments.\n"
                         "- Cryotherapy (freezing) can be used for stubborn cases.\n"
                         "- Wash hands frequently to prevent spreading.",

    "Seborrheic Keratosis": "🩹 Recommendations:\n"
                            "- These are **non-cancerous growths**; removal is optional.\n"
                            "- If irritated, consider laser therapy or freezing treatments.\n"
                            "- Consult a dermatologist if there are sudden changes.",
    "Melanocytic Nevi": "🔍 Recommendations:\n"
                    "- These are **commonly known as moles** and are usually harmless.\n"
                    "- Monitor for **any changes in size, shape, or color**.\n"
                    "- Avoid excessive sun exposure and use sunscreen (SPF 30+).\n"
                    "- If you notice **itching, bleeding, or irregular borders**, consult a dermatologist immediately."

}

transform =  transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])



def get_features(image_path, model):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)
    with torch.no_grad():
        outputs = model(image)
    return outputs[0].cpu().numpy()       


def predict_disease(decision_input):
    return dt_model.predict([decision_input])[0] 

user_symptoms = {}
user_rejected_symptoms = set()
awaiting_symptom = None 
first_input_received = False  


import numpy as np

def convert_disease_to_binary(disease, symptoms_order, disease_symptom_map):
    
    binary_vector = np.zeros(len(symptoms_order), dtype=int)
    if disease in disease_symptom_map:
        for symptom in disease_symptom_map[disease]:
            symptom = symptom.lower()
            if symptom in symptoms_order:  # Ensure symptom is found
                index = symptoms_order.index(symptom)
                binary_vector[index] = 1
            else:
                print(f"Symptom '{symptom}' not found in symptoms_order")
    return binary_vector

# Example usage:
final_disease = ""  # Replace with the actual detected disease
symptom_vector = convert_disease_to_binary(final_disease, symptoms_order, disease_symptom_map)
print("Binary Symptom Vector:", symptom_vector)
 # Track the symptom currently being asked


def get_most_relevant_symptom(remaining_diseases, user_symptoms, user_rejected_symptoms):
    symptom_counts = {}  
    for disease in remaining_diseases:
        for symptom in disease_symptom_map[disease]:
            symptom_lower = symptom.lower()
            if symptom_lower not in user_symptoms and symptom_lower not in user_rejected_symptoms:
                symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
    return max(symptom_counts, key=symptom_counts.get) if symptom_counts else None

def get_possible_diseases(user_symptoms):
    user_positive_symptoms = {s.lower() for s, v in user_symptoms.items() if v}
    matching_diseases = []
    
    for disease, symptoms in disease_symptom_map.items():
        disease_symptoms_set = set(s.lower() for s in symptoms)
        if user_positive_symptoms.issubset(disease_symptoms_set):
            matching_diseases.append(disease)
    
    return matching_diseases if matching_diseases else ["unknown condition"]

@app.route('/')
def serve_root():
    return send_from_directory('EpiBot', 'index.html')

@app.route("/webhook", methods=["POST"])
def webhook():
    global awaiting_symptom, first_input_received   
    data = request.json
    intent = data.get("queryResult", {}).get("intent", {}).get("displayName", "")
    user_input = data.get("queryResult", {}).get("queryText", "").strip().lower()

    image_path = r"D:\myproject\testimages\3_4.jpg"
    image_features = get_features(image_path, model)

    # Extract symptoms from Dialogflow
    symptom_list = data.get("queryResult", {}).get("parameters", {}).get("Symptoms", [])
    if symptom_list:
        for symptom in symptom_list:
            symptom = symptom.lower().strip()
            user_symptoms[symptom] = True  # Store symptoms

            if symptom not in symptoms_order:
                print(f"Warning: Symptom '{symptom}' not found in symptoms_order")  # Debugging

        first_input_received = True
        print("First input symptoms:", user_symptoms)  # Debugging

    if intent == "Describe Symptoms Intent" and first_input_received:
        # Determine possible diseases
        possible_diseases = get_possible_diseases(user_symptoms)
        print(" Possible Diseases:", possible_diseases)  # Debugging

        if len(possible_diseases) == 1:
            final_disease = possible_diseases[0]
            
            # Generate binary symptom vector
            symptom_vector = convert_disease_to_binary(final_disease, symptoms_order, disease_symptom_map)
            print(" Binary Symptom Vector:", symptom_vector)  # Debugging

            input_vector = np.concatenate([image_features, symptom_vector])
            final_prediction = predict_disease(input_vector)
            predicted_disease = class_names[final_prediction]

            print(f" Final Prediction: {predicted_disease}")  # Debugging
            response_text = (
                f"Based on your symptoms, the most likely diagnosis is **{predicted_disease}**.\n\n"
                f"{recommendations.get(predicted_disease, 'Please consult a doctor for further diagnosis.')}"
            )
        else:
            # Find the next most relevant symptom
            next_symptom = get_most_relevant_symptom(possible_diseases, user_symptoms, user_rejected_symptoms)
            if next_symptom:
                awaiting_symptom = next_symptom.lower()
                response_text = f"You may have {', '.join(possible_diseases)}. Do you also have {next_symptom}?"
            else:
                response_text = f"You may have {', '.join(possible_diseases)}. Please consult a doctor for further diagnosis."

        return jsonify({"fulfillmentText": response_text})

    elif intent == "AnswerSymptom":
        answer_list = data.get("queryResult", {}).get("parameters", {}).get("YesNo", [])

        print(f"DEBUG: Awaiting Symptom BEFORE check: {awaiting_symptom}")  # Debugging

        # Handling yes/no responses
        if awaiting_symptom:
            expected_symptom = awaiting_symptom.lower()
            answer = answer_list[0].strip().lower() if answer_list else ""  

            if answer == "yes":
                user_symptoms[expected_symptom] = True
            elif answer == "no":
                user_rejected_symptoms.add(expected_symptom)
                user_symptoms.pop(expected_symptom, None)
            else:
                return jsonify({"fulfillmentText": f"Please answer with 'yes' or 'no'. Do you have {awaiting_symptom}?"})

            awaiting_symptom = None

        # Update symptoms based on multiple inputs (if present)
        if symptom_list and answer_list:
            for symptom, answer in zip(symptom_list, answer_list):
                symptom = symptom.strip().lower()
                answer = answer.strip().lower().replace(",", "")

                if answer == "yes":
                    user_symptoms[symptom] = True
                elif answer == "no":
                    user_rejected_symptoms.add(symptom)
                    user_symptoms.pop(symptom, None)
                else:
                    return jsonify({"fulfillmentText": f"Please respond with yes or no for {symptom}."})

        print(" User Symptoms:", user_symptoms)  # Debugging
        print(" Rejected Symptoms:", user_rejected_symptoms)  # Debugging

        # Recalculate possible diseases
        possible_diseases = get_possible_diseases(user_symptoms)
        print(" Possible Diseases After Update:", possible_diseases)  # Debugging

        if len(possible_diseases) == 1 and possible_diseases[0] != "unknown condition":
            final_disease = possible_diseases[0]

            # Generate binary symptom vector
            symptom_vector = convert_disease_to_binary(final_disease, symptoms_order, disease_symptom_map)
            print(" Binary Symptom Vector:", symptom_vector)  # Debugging

            input_vector = np.concatenate([image_features, symptom_vector])
            final_prediction = predict_disease(input_vector)

            predicted_disease = class_names[final_prediction]
            
            print(f" Final Prediction: {class_names[final_prediction]}")  # Debugging
            response_text = (
                f"Based on your symptoms, the most likely diagnosis is **{predicted_disease}**.\n\n "
                f"{recommendations[class_names[final_prediction]]}"
            )
            awaiting_symptom = None
        else:
            # Ask about the next most relevant symptom
            next_symptom = get_most_relevant_symptom(possible_diseases, user_symptoms, user_rejected_symptoms)
            if next_symptom:
                awaiting_symptom = next_symptom.lower()
                response_text = f"You may have {', '.join(possible_diseases)}. Do you also have {next_symptom}?"
            else:
                response_text = f"You may have {', '.join(possible_diseases)}. Please consult a doctor for further diagnosis."

        print(" Response Text:", response_text)  # Debugging
        return jsonify({"fulfillmentText": response_text})

    return jsonify({"fulfillmentText": "I didn't understand that request."})

SERVICE_ACCOUNT_FILE = r"secure.json"

with open(SERVICE_ACCOUNT_FILE) as f:
    creds = json.load(f)

client = dialogflow.SessionsClient.from_service_account_info(creds)
project_id = creds["project_id"]


@app.route("/send-message", methods=["POST"])
def send_message():
    data = request.json
    user_message = data.get("message")  # Get user message from React
    session_id = data.get("sessionId", "123456")  # Unique session per user

    # Send request to Dialogflow
    session = client.session_path(project_id, session_id)
    text_input = dialogflow.types.TextInput(text=user_message, language_code="en")
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = client.detect_intent(session=session, query_input=query_input)
    print(response)

    bot_response = response.query_result.fulfillment_text
    return jsonify({"response": bot_response})

    
if __name__ == "__main__":
    app.run(debug=True) 

