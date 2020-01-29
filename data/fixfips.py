import csv
import os
from functools import partial

def process_row(column_name, padding, row):
	rowc = {k: v.strip() for k, v in row.items()}
	padme = rowc[column_name]
	rowc[column_name] = padme.zfill(padding) if padme else ""
	return rowc

def read_rows(file, processor):
	rows = []
	headers = []
	reader = csv.DictReader(file)

	for row in reader:
		if not headers:
			headers = [h for h in row.keys()]
		rows.append(processor(row))

	return (headers, rows)

def write_rows(file, headers, rows):
	writer = csv.DictWriter(file, fieldnames=headers, quoting=csv.QUOTE_NONNUMERIC)
	writer.writeheader()
	writer.writerows(rows)

def process_file(file_name, column_name, padding):
	headers, rows = None, None
	input_path = os.path.join('.', file_name)
	output_path = os.path.join('.', 'fixed-' + file_name)

	proc = partial(process_row, column_name, padding)

	with open(input_path, 'r', newline='') as csvfile:
		(headers, rows) = read_rows(csvfile, proc)

	with open(output_path, 'w', newline='') as csvfile:
		write_rows(csvfile, headers, rows)

	os.replace(output_path, input_path)

file_info = [
	('states.csv', 'fips', 2),
	('counties.csv', 'fips', 3),
]

for fi in file_info:
	process_file(*fi)
