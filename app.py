from flask import Flask, request, render_template, jsonify
import requests
import google.generativeai as genai
import pymysql
import re,textwrap
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from twilio.rest import Client

app = Flask(__name__)


# gemini API key
genai.configure(api_key="SECRET_KEY")

#load models
model = joblib.load('static/hospitalization_risk_model.pkl')
loaded_model = joblib.load("static/optimal.pkl")

# twilio configuration
account_sid = 'SID'
auth_token = 'API_TOKEN'
twilio_phone_number = 'PHONE_NUMBER'


db_config = {
    'host': 'hospitaldb.ct4kqsgsqpud.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Ctsnpn2024',  
    'database': 'hospital',
    'cursorclass': pymysql.cursors.DictCursor
}
def get_db_connection():
    connection = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        cursorclass=db_config['cursorclass']
    )
    return connection

# home page
@app.route('/')
def home():
    return render_template("Home.html")

# report generation page
@app.route('/reportgen', methods=['GET', 'POST'])
def reportgen():
    report = None
    if request.method == 'POST':
        visit_id = request.form.get('visit-id')
        if visit_id and visit_id.strip():
            report = format_report(generate_report_text(visit_id))
        else:
            report = "Invalid Visit ID"
    #print(report)
    return render_template("Report Generation.html", report=report)


def generate_report_text(visit_id):
    try:
        appointment_url = f'http://54.89.108.128:8000/appointmenthistory/{visit_id}'
        appointment_response = requests.get(appointment_url)
        print(f"Appointment API Response: {appointment_response.status_code}")
        print(f"Response Content: {appointment_response.content}")
        if appointment_response.status_code != 200 or not appointment_response.content.strip():
            return "Invalid Visit ID"
        appointment_data = appointment_response.json()
        if not appointment_data:
            return "Invalid Visit ID"

        visit_id = appointment_data.get('VisitID')
        patient_id = appointment_data.get('PatientID')
        doctor_id = appointment_data.get('DoctorID')
        cause_of_visit = appointment_data.get('CauseOfVisit')
        symptoms = appointment_data.get('Symptoms')
        medications = appointment_data.get('Medications')
        visit_date = appointment_data.get('VisitDate')

        patient_url = f'http://54.89.108.128:8000/patients/{patient_id}'
        patient_response = requests.get(patient_url)

        print(f"Patient API Response: {patient_response.status_code}")
        print(f"Response Content: {patient_response.content}")

        if patient_response.status_code != 200 or not patient_response.content.strip():
            return "Invalid Patient ID"

        patient_data = patient_response.json()

        if not patient_data:
            return "Invalid Patient ID"

        patient_name = patient_data.get('Name')
        patient_age = patient_data.get('Age')
        patient_gender = patient_data.get('Gender')
        patient_past_history = patient_data.get('PastHistory')

        doctor_url = f'http://54.89.108.128:8000/doctor/{doctor_id}'
        doctor_response = requests.get(doctor_url)

        print(f"Doctor API Response: {doctor_response.status_code}")
        print(f"Response Content: {doctor_response.content}")

        if doctor_response.status_code != 200 or not doctor_response.content.strip():
            return "Invalid Doctor ID"

        doctor_data = doctor_response.json()

        if not doctor_data:
            return "Invalid Doctor ID"

        doctor_name = doctor_data.get('DoctorName')

        prompt_text = (f"visit id: {visit_id}, visit date: {visit_date}, patient name: {patient_name}, "
                       f"patient id: {patient_id}, doctor name: {doctor_name}, doctor id: {doctor_id}, "
                       f"patient age: {patient_age}, patient sex: {patient_gender}, "
                       f"reason for visit: {cause_of_visit}, symptoms: {symptoms}, "
                       f"past medical history: {patient_past_history}, medications: {medications}.")


        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 6000,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction="consice and precise, also explain in layman's terms.Generate a detailed and patient-friendly discharge report that includes explanations for the patient's disease, the reasoning behind the patient's condition based on their current information and past medical history, as well as the rationale for the prescribed medications or treatments. The report should also provide post-discharge instructions, including AI recommendations for temporary lifestyle changes and future prevention measures. Additional information such as past medical history and lab test results should be considered, and if any information is missing, it should be indicated as 'None' or 'Nil.' If only one date is provided, the date of discharge is not required in the report. Do not explain the physical symptoms, but instead, focus on why the recommended medications only were prescribed for the patient and why not similar ones, taking into account their current condition and symptoms, as well as any relevant historical data. Additionally, provide an explanation for why alternative medications serving a similar purpose were not recommended, if applicable. Include the doctor's name and ID in the report."
            )

        chat_session = model.start_chat(
            history=[]
        )

        response = chat_session.send_message(prompt_text)
        return response.text

    except requests.RequestException as e:
        return "An error occurred while fetching the data: " + str(e)
    

def format_report(report_text):
    cleaned_report = re.sub(r'[#*]+', '', report_text)
    cleaned_report = re.sub(r'\s*\n\s*', '\n', cleaned_report).strip()
    formatted_report = ""
    for line in cleaned_report.split('\n'):
        if line.strip():  
            wrapped_line = textwrap.fill(line.strip(), width=80, subsequent_indent="    ")
            formatted_report += wrapped_line + "\n\n"

    return formatted_report.strip()


# about page
@app.route('/about')
def about():
    return render_template('about.html')

# govt schemes page
@app.route('/govtschemes')
def govtschemes():
    return render_template("schemes.html")

@app.route('/govtschemescheck', methods=['GET', 'POST'])
def govtschemecheck():
    patient_id = request.args.get('patientID')
    
    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400
    
    try:
        patient_response = requests.get(f'http://54.89.108.128:8000/patients/{patient_id}')
        patient_data = patient_response.json()
        
        if 'error' in patient_data:
            return jsonify({"error": "Patient not found"}), 404

        age = patient_data.get('Age')
        income = patient_data.get('Income')
        gender = patient_data.get('Gender')
        schemes_response = requests.get('http://54.89.108.128:8000/govtschemes')
        schemes_data = schemes_response.json()
        
        eligible_schemes = []

        for scheme in schemes_data:
            scheme_gender = scheme.get('Gender')
            scheme_lower_age = scheme.get('LowerAge')
            scheme_upper_age = scheme.get('UpperAge')
            scheme_lower_income = scheme.get('LowerIncome')
            scheme_upper_income = scheme.get('UpperIncome')

            if (age >= scheme_lower_age and age <= scheme_upper_age and
                (scheme_gender == 'All' or scheme_gender == gender) and
                (age < 18 or (income is not None and income >= scheme_lower_income and income <= scheme_upper_income))):
                eligible_schemes.append(scheme.get('SchemeName'))

        if eligible_schemes:
            return jsonify(eligible_schemes)
        else:
            return jsonify({"message": "No suitable schemes found"})
    
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
# patient history page
@app.route('/patienthistory')
def patienthistory():
    return render_template('history.html')

@app.route('/fetch_patient_reports', methods=['GET'])
def fetch_patient_reports():
    patient_id = request.args.get('patientID')
    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400
    
    try:
        url = f'http://54.89.108.128:8000/patientreport/{patient_id}'
        response = requests.get(url)
        report_data = response.json()

        if not report_data:
            return jsonify({"error": "No reports found for the given patient ID"})

        formatted_reports = []
        for report in report_data:
            generated_report = format_report(report.get('GeneratedReport', 'No content available'))
            formatted_reports.append({'GeneratedReport': generated_report})

        return jsonify(formatted_reports)
    
    except requests.RequestException as e:
        return jsonify({"error": f"Error fetching reports: {str(e)}"}), 500
    
def fetch_patient_info(visit_id):
    try:
        appointment_url = f'http://54.89.108.128:8000/appointmenthistory/{visit_id}'
        appointment_response = requests.get(appointment_url)
        if appointment_response.status_code != 200 or not appointment_response.content.strip():
            return "Invalid Visit ID"

        appointment_data = appointment_response.json()
        if not appointment_data:
            return "Invalid Visit ID"

        visit_id = appointment_data.get('VisitID')
        patient_id = appointment_data.get('PatientID')
        doctor_id = appointment_data.get('DoctorID')
        cause_of_visit = appointment_data.get('CauseOfVisit')
        symptoms = appointment_data.get('Symptoms')
        medications = appointment_data.get('Medications')
        visit_date = appointment_data.get('VisitDate')

    
        patient_url = f'http://54.89.108.128:8000/patients/{patient_id}'
        patient_response = requests.get(patient_url)
        if patient_response.status_code != 200 or not patient_response.content.strip():
            return "Invalid Patient ID"

        patient_data = patient_response.json()
        if not patient_data:
            return "Invalid Patient ID"

        patient_name = patient_data.get('Name')
        patient_age = patient_data.get('Age')
        patient_gender = patient_data.get('Gender')
        patient_past_history = patient_data.get('PastHistory')

        doctor_url = f'http://54.89.108.128:8000/doctor/{doctor_id}'
        doctor_response = requests.get(doctor_url)
        if doctor_response.status_code != 200 or not doctor_response.content.strip():
            return "Invalid Doctor ID"

        doctor_data = doctor_response.json()
        if not doctor_data:
            return "Invalid Doctor ID"

        doctor_name = doctor_data.get('DoctorName')

        return (f"Patient information: visit id: {visit_id}, visit date: {visit_date}, patient name: {patient_name}, "
                f"patient id: {patient_id}, doctor name: {doctor_name}, doctor id: {doctor_id}, "
                f"patient age: {patient_age}, patient sex: {patient_gender}, "
                f"reason for visit: {cause_of_visit}, symptoms: {symptoms}, "
                f"past medical history: {patient_past_history}, medications: {medications}.")

    except requests.RequestException as e:
        return f"An error occurred while fetching the data: {str(e)}"


# feedback page
@app.route('/feedback')
def feedback():
    return render_template("feedback.html")

@app.route('/start-feedback', methods=['POST'])
def start_feedback():
    visit_id = request.form.get('visitId')

    if not visit_id:
        return jsonify({'error': 'Visit ID is required'}), 400
    
    generation_config = {
    "temperature": 0.25,
    "top_p": 0.80,
    "top_k": 64,
    "max_output_tokens": 2000,
    "response_mime_type": "text/plain",
    }
    system_instruction = """You are Ava. Your task is to ask the patient up to 4 personalized feedback questions. Start by greeting the patient and asking them to rate their experience from 1 to 10. Once they provide a rating, don’t ask for it again. Tailor your follow-up questions based on their rating: use positive language for ratings of 6 or above, and empathetic language for ratings of 5 or below. Ask about their experience and what could be improved, while remembering their previous responses. After 4 questions, thank them for their feedback and let them know it is valuable to 'Serene' hospital services.  Avoid repeating questions and only focus on their feedback, without asking for another rating. you can provide details like doctorname,medications,symptoms,etc from the info available to you"""


    patient_info = fetch_patient_info(visit_id)

    if "Invalid" in patient_info:
        return jsonify({'error': patient_info}), 400

    updated_system_instruction = system_instruction + patient_info

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=updated_system_instruction
    )

    chat_session = model.start_chat(history=[])
    initial_message = chat_session.send_message("Hello! I'm Ava, here to gather your feedback about your recent experience at Serene hospital. How would you rate your overall experience on a scale of 1 to 10?")

    return jsonify({'success': True, 'message': initial_message.text, 'system_instruction': updated_system_instruction})

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.form
    user_message = data.get('message')
    exchange_count = int(data.get('exchange_count', 0))
    system_instruction = data.get('system_instruction')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    if exchange_count >= 5:
        return jsonify({'response': "Thank you for your feedback. The conversation has ended."})
    
    generation_config = {
    "temperature": 0.25,
    "top_p": 0.80,
    "top_k": 64,
    "max_output_tokens": 2000,
    "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=system_instruction
    )
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(user_message)

    if "feedback not received" in response.text.lower():
        response_text = "Feedback not received. Please provide your feedback to continue."
    else:
        response_text = response.text

    print(f"User Message: {user_message}")
    print(f"System Instruction: {system_instruction}")
    print(f"Model Response: {response_text}")

    return jsonify({'response': response_text})


# appointment booking page
@app.route('/book')
def appointment():
    return render_template("book.html")

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    patient_id = request.form.get('patientId')
    date = request.form.get('date')
    doctor_id = request.form.get('doctorId')

    url = f"http://54.89.108.128:8000/appointments/{date}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            data = data[0]
            
            slot_times = {
                1: "6:30PM",
                2: "7:00PM",
                3: "7:30PM",
                4: "8:00PM",
                5: "8:30PM"
            }
            
            available_slots = {
                index + 1: slot_times[index + 1] for index, slot in enumerate(
                    [data['slot1'], data['slot2'], data['slot3'], data['slot4'], data['slot5']])
                    if slot == 0
            }
            
            return render_template('book.html', 
                                   patient_id=patient_id, 
                                   date=date, 
                                   doctor_id=doctor_id,
                                   available_slots=available_slots)
        else:
            return "Unexpected data format", 500
    
    except requests.RequestException:
        return "Failed to fetch data from the appointments service", 500
    except ValueError:
        return "Failed to decode response from the appointments service", 500

@app.route('/book_slot', methods=['POST'])
def book_slot():
    patient_id = request.form.get('patientId')
    date = request.form.get('date')
    doctor_id = request.form.get('doctorId')
    selected_slot = int(request.form.get('selectedSlot'))

    def get_next_visit_id():
        connection = pymysql.connect(**db_config)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT MAX(VisitID) AS max_id FROM AppointmentHistory")
                result = cursor.fetchone()
                max_id = result['max_id'] if result['max_id'] is not None else 1011
                next_id = max_id + 1
        finally:
            connection.close()
        return next_id

    def time_to_minutes(time_str):
        time_str = time_str.replace('PM', '').strip()
        h, m = map(int, time_str.split(':'))
        h += 12
        return h * 60 + m

    def minutes_to_time(minutes):
        hours, mins = divmod(minutes, 60)
        time = datetime(1, 1, 1, hours, mins)
        return time.strftime("%I:%M %p")

    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT slot1, slot2, slot3, slot4, slot5, avgConsultTime FROM Appointment WHERE visitDate = %s", (date,))
            row = cursor.fetchone()

            if row is None:
                return "No data found for the specified date", 500

            slot_mapping = {
                1: '6:30PM',
                2: '7:00PM',
                3: '7:30PM',
                4: '8:00PM',
                5: '8:30PM'
            }

            available_slots = {index + 1: slot_mapping[index + 1] for index, slot in enumerate(
                [row['slot1'], row['slot2'], row['slot3'], row['slot4'], row['slot5']])
                if slot == 0
            }

            if selected_slot not in available_slots:
                return render_template('book.html', 
                                       patient_id=patient_id, 
                                       date=date, 
                                       doctor_id=doctor_id,
                                       available_slots=available_slots,
                                       visit_id=" *** Please re-enter a valid slot number ***")
            
            visit_id = get_next_visit_id()
            
            sql_insert = """
            INSERT INTO AppointmentHistory (VisitID, PatientID, DoctorID, SlotNumber, VisitDate)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert, (visit_id, patient_id, doctor_id, selected_slot, date))
            
            slot_column = f'slot{selected_slot}'
            sql_update = f"""
            UPDATE Appointment
            SET {slot_column} = 1
            WHERE visitDate = %s
            """
            cursor.execute(sql_update, (date,))
            
            booked_slots_before = sum(1 for i in range(1, selected_slot) if row[f'slot{i}'] == 1)
            empty_slots_before = sum(1 for i in range(1, selected_slot) if row[f'slot{i}'] == 0)
            avg_consult_time = row['avgConsultTime']
            appointment_start_time = time_to_minutes(slot_mapping[selected_slot])

            total_slots = 5
            sample_input = pd.DataFrame([[total_slots, booked_slots_before, empty_slots_before, avg_consult_time, appointment_start_time]],
                                        columns=['Total Slots', 'Number of Booked Slots Before Your Slot', 'Number of Empty Slots Before Your Slot', 'Average Consulting Time', 'Appointment Start Time'])
            
            predicted_time = loaded_model.predict(sample_input)
            predicted_time_minutes = int(predicted_time[0])
            predicted_time_formatted = minutes_to_time(predicted_time_minutes)

            connection.commit()

            # Fetch patient details
            patient_url = f"http://54.89.108.128:8000/patients/{patient_id}"
            patient_response = requests.get(patient_url)
            patient_response.raise_for_status()
            patient_data = patient_response.json()
            patient_name = patient_data.get('Name')
            patient_contact_number = "+918903106677"

            # Fetch doctor details
            doctor_url = f"http://54.89.108.128:8000/doctor/{doctor_id}"
            doctor_response = requests.get(doctor_url)
            doctor_response.raise_for_status()
            doctor_data = doctor_response.json()
            doctor_name = doctor_data.get('DoctorName')

            # Formulate the message
            message = (f"Dear {patient_name},\n\n"
                       f"Your appointment with Dr. {doctor_name} is scheduled for {date}.\n"
                       f"Visit ID: {visit_id}\n"
                       f"Consultation Time: {predicted_time_formatted}.\n\n"
                       f"Thank you for choosing our services.\n"
                       f"Best regards,\nAva")


            # send sms alerts for the booked appoitment
            client = Client(account_sid, auth_token)

            def send_follow_up_sms(patient_name, mobile_number, follow_up_message):
                message = client.messages.create(
                    body=f"Hello {patient_name}, {follow_up_message}",
                    from_=twilio_phone_number,
                    to=mobile_number
                )
                print(f"Message sent to {patient_name} at {mobile_number}. SID: {message.sid}")

            follow_up_message = f"Your appointment with {doctor_name} is scheduled for {date} at {predicted_time_formatted}. Visit ID: {visit_id}."
            send_follow_up_sms(patient_name, patient_contact_number, follow_up_message)
            
            return render_template('book.html', 
                                   patient_id=patient_id, 
                                   date=date, 
                                   doctor_id=doctor_id,
                                   available_slots=available_slots,
                                   visit_id=f"Appointment Booked Successfully               *** Visit ID: {visit_id} ***",
                                   consultation_time=f"Predicted Optimal Consultation Time: {predicted_time_formatted}")
    except pymysql.MySQLError:
        connection.rollback()
        return "Database error occurred", 500
    except requests.RequestException:
        return "Failed to fetch data from the external service", 500
    except Exception as e:
        return f"An unexpected error occurred: {e}", 500
    finally:
        connection.close()



#hospitalization risk prediction page
@app.route('/risk')
def risk():
    return render_template("risk.html")

@app.route('/calculate-risk', methods=['POST'])
def calculate_risk():
    try:
        data = request.json
        age = int(data.get('age'))
        gender = int(data.get('gender'))
        height = int(data.get('height'))
        weight = int(data.get('weight'))
        smoking_drinking_score = int(data.get('smokingDrinkingScore'))
        daily_steps = int(data.get('dailySteps'))
        nutrition_score = int(data.get('nutritionScore'))
        sleeping_hours = int(data.get('sleepingHours'))
        stress_levels = int(data.get('stressLevels'))

        height_m = height / 100  
        bmi = weight / (height_m ** 2)

        input_features = np.array([[
            age, gender, bmi, smoking_drinking_score, 
            daily_steps, nutrition_score, sleeping_hours, stress_levels
        ]])
        risk_prediction = model.predict(input_features)[0]
        risk_percentage = round(risk_prediction * 100, 2)
        return jsonify({'risk': f'{risk_percentage}%'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


# general inquiry bot page
@app.route('/chat')
def index():
    return render_template('chat.html')

@app.route('/send-chat', methods=['POST'])
def send_chat():
    generation_config = {
        "temperature": 0.35,
        "top_p": 0.50,
        "top_k": 57,
        "max_output_tokens": 1024,
        "response_mime_type": "text/plain",
    }
    system_instruction = (
        """Introduce yourself As Ava in your first response, your goal is to provide clear, supportive, and concise medical advice. 
        Respond to queries in a calm and empathetic manner. 
        Avoid long explanations and stay focused on comfort and clarity.and also, avoid saying  you are not a medical expert and help users on their medical queries. 
        Also if they inquire about features ("Appointment Booking","Report Generation","Patient History","Scheme Eligiblity Check","Hospitalization Risk Calculator","Feedback")
        ask them to look these info on our website ,else if they inquire outside these features ask them to contact our helpline number for 
        more detailed and personalized support,also if you find they are going to end the conversation make sure to 
        tell them about our features ("Appointment Booking","Report Generation","Patient History","Scheme Eligiblity Check","Hospitalization Risk Calculator","Feedback")
        """
    )
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config, system_instruction=system_instruction)
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(user_message)
    
    return jsonify({'response': response.text})

@app.route('/initial-message', methods=['GET'])
def initial_message():
    generation_config = {
        "temperature": 0.35,
        "top_p": 0.50,
        "top_k": 57,
        "max_output_tokens": 1024,
        "response_mime_type": "text/plain",
    }
    system_instruction = (
        """Introduce yourself As Ava in your first response, your goal is to provide clear, supportive, and concise medical advice. 
        Respond to queries in a calm and empathetic manner. 
        Avoid long explanations and stay focused on comfort and clarity.and also, avoid saying  you are not a medical expert and help users on their medical queries. 
        Also if they inquire about features ("Appointment Booking","Report Generation","Patient History","Scheme Eligiblity Check","Hospitalization Risk Calculator","Feedback")
        ask them to look these info on our website ,else if they inquire outside these features ask them to contact our helpline number for 
        more detailed and personalized support,also if you find they are going to end the conversation make sure to 
        tell them about our features ("Appointment Booking","Report Generation","Patient History","Scheme Eligiblity Check","Hospitalization Risk Calculator","Feedback")
        """
    )
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config, system_instruction=system_instruction)
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message("Hello, I am Ava, your personalized virtual assistant.")
    
    return jsonify({'response': response.text})


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
