import csv
import json

def csv_to_json(csv_file_path, json_file_path):
    data = {"probabilities": []}
    
    with open(csv_file_path, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        header = next(csv_reader)
        
        for row in csv_reader:
            interaction_type = row[0]
            probabilities = {header[i]: int(row[i]) for i in range(1, len(row))}
            data["probabilities"].append({
                "interaction_type": interaction_type,
                "probabilities": probabilities
            })
            
    with open(json_file_path, mode='w') as json_file:
        json.dump(data, json_file, indent=4)

csv_file_path = 'robot_notengd_hri_probabilities.csv'
json_file_path = 'robot_notengd_hri_probabilities.json'
csv_to_json(csv_file_path, json_file_path)
