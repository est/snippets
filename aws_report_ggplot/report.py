import csv
import datetime


writer = csv.writer(open('report_out.csv', 'w'))


fmt1 = '%m/%d/%y %H:%M:%S'

with open('report.csv') as csvfile:
    reader = csv.reader(csvfile)
    
    # first row
    for i, row in enumerate(reader):
        # Service, Operation, UsageType, Resource, StartTime, EndTime, UsageValue
        try:
            operation = row[1]
            usage_type = row[2]
            resource = row[3]
            time = row[4]
            if i>0:
                time = datetime.datetime.strptime(time, fmt1)
                time = time.date().isoformat()
            usage_value = row[6]
            if usage_type == 'DataTransfer-Out-Bytes' and operation == 'GetObject':
                


                writer.writerow([operation, usage_type, resource, time, usage_value])
        except IndexError:
            print type(row), row

