import pandas as pd 
import csv
import datetime
import statistics
import os
import sys


class Patient:

	def __init__(self, patient_id, arrest_date, done_date):
		self.id = patient_id
		self.arrest_date = arrest_date
		self.done_date = done_date
		self.drug_data = {
							'drugs':[],
							'doses':[],
							'units':[],
							'administered_times':[],
							'strengths': [],
							'volumes':[]
						}
		self.drugs = set()
		self.fentanyl = 0
		self.dexmedetomidine = 0
		self.propofol = 0
		self.ketamine = 0
		self.remifentanil = 0
		self.midazolam = 0

	def update_drug(self, drug, dose, unit, drug_administered_time, strength, volume):
		if drug not in self.drugs:
			self.drugs.add(drug)	
		self.drug_data['drugs'].append(drug)
		self.drug_data['doses'].append(dose)
		self.drug_data['units'].append(unit)
		self.drug_data['administered_times'].append(drug_administered_time)
		self.drug_data['strengths'].append(strength)
		self.drug_data['volumes'].append(volume)
				

def midazolam_eq(drug, dose):
	if drug == 'lorazepam':
		try:
			return dose*2
		except TypeError:
			dose = 0
			return dose
	elif drug == 'diazepam':
		try:
			return dose*0.25
		except TypeError:
			dose = 0
			return dose
	else:
		return dose


def fix_units(dose, unit, strength, volume):
	if unit == 'mL':
		try:
			return dose*strength/volume
		except ZeroDivisionError:
			dose = 0
			return dose
	elif unit =='mL/hr':
		try:
			return dose*strength/volume
		except ZeroDivisionError:
			dose = 0
			return dose
	elif unit=='mcg':
		return dose
	elif unit=='mcg/hr':
		return dose
	elif unit=='mcg/kg/hr':
		return dose*70
	elif unit=='mcg/kg/min':
		return dose*70*60
	elif unit=='mg':
		return dose
	elif unit=='mg/day':
		return dose/24
	elif unit=='mg/hr':
		return dose
	elif unit=='mg/kg':
		return dose*70
	elif unit=='mg/kg/hr':
		return dose*70
	elif unit=='mg/mL':
		return dose*strength*volume
	elif unit=='mg/min':
		return dose*60
	else:
		dose = 0
		return dose

def calculate_drug_dose_hour(single_drug_data, patient, drug_original):
	benzos = ['lorazepam', 'diazepam']
	units = ('mg', 'mcg')
	output = zip(
				single_drug_data['doses'],
				single_drug_data['units'],
				single_drug_data['strengths'],
				single_drug_data['volumes']
				)

	average_drug = []
	for dose, unit, strength, volume in output:
		dose = fix_units(dose, unit, strength, volume)
		if drug_original in benzos:
			dose = midazolam_eq(drug_original, dose)
			if unit not in units:
				average_drug.append(dose)
			else:
				current_value = getattr(patient, 'midazolam')
				new_value = current_value + dose
				setattr(patient, 'midazolam', new_value)
		else:
			if unit not in units:
				average_drug.append(dose)
			else:
				current_value = getattr(patient, drug_original)
				new_value = current_value + dose
				setattr(patient, drug_original, new_value)

	if drug_original in benzos:
		drug_original = 'midazolam'
	current_value = getattr(patient, drug_original)
	try:
		new_value = current_value + statistics.mean(average_drug)
	except (statistics.StatisticsError, TypeError):
		pass
	else:
		setattr(patient, drug, new_value)	

def write_output(patients):
	with open('final_output.csv', 'w', newline='') as f:
		csv_writer = csv.writer(f)
		csv_writer.writerow(['patient_id', 'arrest_date', 'done_date', 'fentanyl (mcg)', 'dexmedetomidine (mcg)', 'propofol (mcg)', 'ketamine (mg)', 'remifentanil (mcg)', 'midazolam_eq (mg)'])
		for patient in patients:
			csv_writer.writerow([
								patient.id,
								patient.arrest_date,
								patient.done_date,
								patient.fentanyl,
								patient.dexmedetomidine,
								patient.propofol,
								patient.ketamine,
								patient.remifentanil,
								patient.midazolam
								])

def check_drug(temp_data, patient):
	drug_list = 'fentanyl remifentanil propofol ketamine dexmedetomidine lorazepam  midazolam'.split()
	for drug_original in drug_list:
		output = zip(
				temp_data['drugs'],
				temp_data['doses'],
				temp_data['units'],
				temp_data['administered_times'],
				temp_data['strengths'],
				temp_data['volumes']
				)
		single_drug_data = {
							'doses':[], 
							'units':[],
							'strengths':[],
							'volumes':[]
							}
		for drug, dose, unit, administered_time, strength, volume in output:
			if drug == drug_original:
				single_drug_data['doses'].append(dose)
				single_drug_data['units'].append(unit)
				single_drug_data['strengths'].append(strength)
				single_drug_data['volumes'].append(volume)
		if len(single_drug_data['doses']) == 0:
			continue
		else:
			calculate_drug_dose_hour(single_drug_data, patient, drug_original)

os.chdir(r'C:\Users\ANDREW\Desktop\work_dir')
df = pd.read_stata('final_data.dta')
df.to_csv('final_data.csv')

patients = []
patient_ids = set()
with open('final_data.csv') as f:
	csv_reader = csv.DictReader(f)
	for patient in csv_reader:
		patient_id = patient['id']

		drug_name_split = patient['drug_name'].split()
		drug = drug_name_split[0].lower()
		if patient['drug_name'].endswith('mL'):
			strength = int(drug_name_split[1].replace(',' , ''))
			volume = int(drug_name_split[-2].replace(',' , ''))
		else:
			strength = 0
			volume = 0
		try:
			dose = float(patient['dose'])
		except ValueError:
			dose = 0
		unit = patient['dose_unit'].strip()
		drug_administered_time = patient['timestamp']#01/24/2014 20:000
		drug_administered_time = datetime.datetime.strptime(drug_administered_time, '%Y-%m-%d %X')
		arrest_date = patient['arrestdate']#December 29, 2012
		arrest_date = datetime.datetime.strptime(arrest_date, '%Y-%m-%d %X')
		if patient['deathdate']:
			date_done = patient['deathdate']#January 31, 2014
			date_done = datetime.datetime.strptime(date_done, '%Y-%m-%d %X')
		else:
			date_done = patient['date_fol_com']#January 31, 2014
			try:
				date_done = datetime.datetime.strptime(date_done, '%Y-%m-%d %X')
			except ValueError:
				continue
		difference = date_done - arrest_date
		if difference.total_seconds() < 259200:
			continue
		difference = drug_administered_time - arrest_date
		if difference.total_seconds() > 259200:
			continue
		if patient_id not in patient_ids:
			patient = Patient(patient_id, arrest_date, date_done)
			patient.update_drug(drug, dose, unit, drug_administered_time, strength, volume)
			patients.append(patient)
			patient_ids.add(patient_id)
		else:
			patient = patients[-1]
			patient.update_drug(drug, dose, unit, drug_administered_time, strength, volume)


for patient in patients:
	arrest_date = patient.arrest_date
	for hour in range(72):
		temp_data = {
					'drugs':[],
					'doses':[],
					'units':[],
					'administered_times':[],
					'strengths': [],
					'volumes':[]
					}
		output = zip(
				patient.drug_data['drugs'],
				patient.drug_data['doses'],
				patient.drug_data['units'],
				patient.drug_data['administered_times'],
				patient.drug_data['strengths'],
				patient.drug_data['volumes']
				)
		for drug, dose, unit, administered_time, strength, volume in output:
			if administered_time >= arrest_date+datetime.timedelta(hours=hour) and administered_time < arrest_date+datetime.timedelta(hours=hour+1):
				temp_data['drugs'].append(drug)
				temp_data['doses'].append(dose)
				temp_data['units'].append(unit)
				temp_data['administered_times'].append(administered_time)
				temp_data['strengths'].append(strength)
				temp_data['volumes'].append(volume)
		if len(temp_data['doses']) == 0:
			continue
		else:
			check_drug(temp_data, patient)
write_output(patients)
os.remove('final_data.csv')